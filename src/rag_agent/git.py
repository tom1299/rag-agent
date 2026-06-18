import base64
import os
import re
import subprocess
import sys
import threading
from dataclasses import dataclass
from difflib import SequenceMatcher
from enum import Enum, auto
from pathlib import Path
from typing import Optional
from urllib.parse import quote


class AuthMethod(Enum):
    NONE = auto()
    TOKEN = auto()   # OAuth2 / personal access token
    BASIC = auto()   # username + password
    SSH = auto()     # SSH key file


@dataclass
class GitAuth:
    method: AuthMethod = AuthMethod.NONE
    token: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    ssh_key_path: Optional[Path] = None

    def secrets(self) -> list[str]:
        return [s for s in [self.token, self.password, self.username] if s]


# ---------------------------------------------------------------------------
# Sanitization
# ---------------------------------------------------------------------------

def _variants(secret: str) -> list[str]:
    """Return plain, base64-encoded, and URL-encoded variants of a secret."""
    return [
        secret,
        base64.b64encode(secret.encode()).decode(),
        quote(secret, safe=""),
    ]


def _similar(candidate: str, secret: str, threshold: float) -> bool:
    if not candidate or not secret:
        return False
    length_ratio = len(candidate) / len(secret)
    if not (0.5 <= length_ratio <= 2.0):
        return False
    return SequenceMatcher(None, candidate, secret).ratio() >= threshold


def _sanitize(text: str, secrets: list[str], threshold: float = 0.8) -> str:
    """
    Replace all occurrences of secrets (and their encoded variants) in text.
    Also fuzzy-replaces words that are suspiciously similar to long secrets.
    Whitespace structure is preserved.
    """
    all_variants = [v for s in secrets if s for v in _variants(s)]

    # Exact replacement (handles plain, base64, URL-encoded forms)
    for variant in all_variants:
        if variant:
            text = text.replace(variant, "***")

    # Fuzzy replacement — only for secrets long enough to be meaningful
    long_secrets = [s for s in secrets if s and len(s) >= 8]
    if not long_secrets:
        return text

    # Split preserving whitespace so we can rejoin without losing newlines
    parts = re.split(r"(\s+)", text)
    sanitized_parts = []
    for part in parts:
        if re.fullmatch(r"\s+", part):
            sanitized_parts.append(part)
        elif any(_similar(part, s, threshold) for s in long_secrets):
            sanitized_parts.append("***")
        else:
            sanitized_parts.append(part)

    return "".join(sanitized_parts)


# ---------------------------------------------------------------------------
# Streaming
# ---------------------------------------------------------------------------

def _stream_sanitized(stream, secrets: list[str], out) -> None:
    """Read lines from stream, sanitize, and write to out in real-time."""
    for line in iter(stream.readline, ""):
        out.write(_sanitize(line, secrets))
        out.flush()
    stream.close()


# ---------------------------------------------------------------------------
# Auth injection
# ---------------------------------------------------------------------------

def _inject_auth(url: str, auth: GitAuth) -> tuple[str, dict]:
    """Return (url_with_credentials, extra_env_vars)."""
    env: dict[str, str] = {}

    match auth.method:
        case AuthMethod.TOKEN:
            prefix, rest = url.split("://", 1)
            url = f"{prefix}://oauth2:{auth.token}@{rest}"

        case AuthMethod.BASIC:
            prefix, rest = url.split("://", 1)
            encoded_username = quote(auth.username, safe="")
            encoded_password = quote(auth.password, safe="")
            url = f"{prefix}://{encoded_username}:{encoded_password}@{rest}"

        case AuthMethod.SSH:
            env["GIT_SSH_COMMAND"] = (
                f"ssh -i {auth.ssh_key_path} "
                "-o StrictHostKeyChecking=no "
                "-o IdentitiesOnly=yes"
            )

        case AuthMethod.NONE:
            pass

    return url, env


# All known git trace environment variables.
GIT_TRACE_VARS: frozenset[str] = frozenset({
    "GIT_TRACE",
    "GIT_TRACE2",
    "GIT_TRACE2_EVENT",
    "GIT_TRACE2_PERF",
    "GIT_TRACE_PACKET",
    "GIT_TRACE_PACK_ACCESS",
    "GIT_TRACE_PERFORMANCE",
    "GIT_TRACE_SETUP",
    "GIT_TRACE_SHALLOW",
    "GIT_CURL_VERBOSE",
})

# ---------------------------------------------------------------------------
# Clone
# ---------------------------------------------------------------------------

def clone_repo(
    url: str,
    dest: Path,
    depth: int = 1,
    ref: Optional[str] = None,
    auth: Optional[GitAuth] = None,
    trace_vars: Optional[set[str]] = None,
) -> None:
    """
    Clone a git repository to dest.

    All git output is streamed to stdout/stderr in real-time with secrets
    redacted (exact, encoded, and fuzzy variants).

    Args:
        url:        Repository URL (https or ssh).
        dest:       Destination directory.
        depth:      Shallow clone depth (default 1).
        ref:        Branch or tag to clone (default: remote HEAD).
        auth:       Authentication credentials.
        trace_vars: Git trace environment variables to enable (set to "1").
                    See GIT_TRACE_VARS for all available names.
                    Example: {"GIT_TRACE", "GIT_CURL_VERBOSE"}

    Raises:
        RuntimeError: If git exits with a non-zero return code.
    """
    auth = auth or GitAuth()
    url, extra_env = _inject_auth(url, auth)
    secrets = auth.secrets()

    trace_env = {var: "1" for var in (trace_vars or [])}

    cmd = [
        "git", "clone",
        "--verbose",
        "--progress",
        f"--depth={depth}",
        "--single-branch",
    ]
    if ref:
        cmd += ["--branch", ref]
    cmd += [url, str(dest)]

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env={
            **os.environ,
            "GIT_TERMINAL_PROMPT": "0",  # disable stdin credential prompt
            "GIT_ASKPASS": "echo",        # disable GUI/askpass credential popup
            **trace_env,
            **extra_env,
        },
    )

    stdout_thread = threading.Thread(
        target=_stream_sanitized, args=(process.stdout, secrets, sys.stdout)
    )
    stderr_thread = threading.Thread(
        target=_stream_sanitized, args=(process.stderr, secrets, sys.stderr)
    )
    stdout_thread.start()
    stderr_thread.start()
    stdout_thread.join()
    stderr_thread.join()

    process.wait()
    if process.returncode != 0:
        raise RuntimeError(f"Git clone failed with exit code {process.returncode}")
