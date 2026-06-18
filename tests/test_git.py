import os
import tempfile
import unittest
from pathlib import Path

from dotenv import load_dotenv

from rag_agent.git import AuthMethod, GitAuth, GIT_TRACE_VARS, clone_repo

load_dotenv()

PUBLIC_REPO_URL = "https://github.com/CICDior/fleet-infra"
PRIVATE_REPO_URL = os.getenv("PRIVATE_REPO_URL", "https://github.com/tom1299/private")


class TestClonePublicRepo(unittest.TestCase):
    """Tests for cloning a public repository without authentication."""

    def test_clone_default_branch(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "fleet-infra"
            clone_repo(url=PUBLIC_REPO_URL, dest=dest, trace_vars=GIT_TRACE_VARS)
            self.assertTrue(dest.exists())
            self.assertTrue((dest / ".git").exists())

    def test_clone_creates_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "fleet-infra"
            clone_repo(url=PUBLIC_REPO_URL, dest=dest, trace_vars=GIT_TRACE_VARS)
            contents = list(dest.iterdir())
            self.assertGreater(len(contents), 0, "Cloned repository should not be empty")

    def test_clone_shallow_depth(self):
        """Shallow clone should result in exactly one commit in the log."""
        import subprocess

        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "fleet-infra"
            clone_repo(url=PUBLIC_REPO_URL, dest=dest, depth=1, trace_vars=GIT_TRACE_VARS)
            result = subprocess.run(
                ["git", "-C", str(dest), "rev-list", "--count", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertEqual(result.stdout.strip(), "1")


class TestClonePrivateRepo(unittest.TestCase):
    """Tests for cloning a private repository using a GitHub token."""

    def setUp(self):
        self.token = os.getenv("GITHUB_TOKEN")
        self.username = os.getenv("GITHUB_USERNAME")
        if not self.token:
            self.skipTest("GITHUB_TOKEN not set — skipping private repo tests")

    def test_clone_with_token(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "private"
            auth = GitAuth(method=AuthMethod.TOKEN, token=self.token)
            clone_repo(url=PRIVATE_REPO_URL, dest=dest, auth=auth, trace_vars=GIT_TRACE_VARS)
            self.assertTrue(dest.exists())
            self.assertTrue((dest / ".git").exists())

    def test_clone_with_basic_auth(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "private"
            auth = GitAuth(
                method=AuthMethod.BASIC,
                username=self.username,
                password=self.token,  # GitHub requires token as password
            )
            clone_repo(url=PRIVATE_REPO_URL, dest=dest, auth=auth, trace_vars=GIT_TRACE_VARS)
            self.assertTrue(dest.exists())
            self.assertTrue((dest / ".git").exists())

    def test_clone_fails_without_auth(self):
        github_token_set = "GITHUB_TOKEN" in os.environ
        if github_token_set:
            os.environ.pop("GITHUB_TOKEN", None)  # Ensure token is not set

        try:
            with tempfile.TemporaryDirectory() as tmp:
                dest = Path(tmp) / "private"
                with self.assertRaises(RuntimeError):
                    clone_repo(url=PRIVATE_REPO_URL, dest=dest, trace_vars=GIT_TRACE_VARS)
        finally:
            if github_token_set:
                os.environ["GITHUB_TOKEN"] = self.token  # Restore token for other tests
