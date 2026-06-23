import asyncio
import logging
import socket
from pathlib import Path
from io import StringIO

from dotenv import load_dotenv

import time
from threading import Thread

import httpx

from a2a.client import A2ACardResolver

from a2a.client import ClientConfig, create_client
from a2a.helpers import new_text_message
from a2a.types.a2a_pb2 import Role, SendMessageRequest

from rag_agent.a2a.server import start_server

import pytest

load_dotenv()


def wait_for_port(host: str, port: int, timeout: float = 30.0, poll_interval: float = 0.1) -> None:
    """Wait until a TCP port is accepting connections or raise TimeoutError."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1.0):
                return
        except OSError:
            time.sleep(poll_interval)

    raise TimeoutError(f"Timed out waiting for {host}:{port} to become available after {timeout}s")


@pytest.fixture(scope='session', autouse=True)
def start_rage_agent_server():
    # TODO: Catpure logging is a bit awkward, find a better solution: E.g. pass logger to server.
    server_log_output = StringIO()

    handler = logging.StreamHandler(server_log_output)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter("%(levelname)s:%(name)s:%(message)s"))

    root_logger = logging.getLogger()
    http_log_logger = logging.getLogger("http_log")

    previous_root_level = root_logger.level
    previous_http_log_level = http_log_logger.level

    root_logger.setLevel(logging.DEBUG)
    http_log_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(handler)

    thread = Thread(
        target=start_server,
        kwargs={"document_path": Path("/home/treuhl/git/github/rag-agent/test-data/software-engineering-frame-conditions")},
        daemon=True,
    )
    thread.start()
    wait_for_port("127.0.0.1", 9998, timeout=30.0)

    yield

    root_logger.removeHandler(handler)
    root_logger.setLevel(previous_root_level)
    http_log_logger.setLevel(previous_http_log_level)

    print("\n--- Server logs ---")
    print(server_log_output.getvalue())

async def get_agent_card():

    async with httpx.AsyncClient() as httpx_client:
        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url='http://127.0.0.1:9998',
        )
        public_agent_card = await resolver.get_agent_card()
        print('\nSuccessfully fetched the public agent card:')

    return public_agent_card

async def send_message(text_query: str = 'Hi there'):
    public_agent_card = await get_agent_card()
    print('\n--- Public Agent Card - Non-Streaming Call ---')

    print('\nInitializing a non-streaming client.')
    async with httpx.AsyncClient(timeout=httpx.Timeout(connect=5.0, read=120.0, write=120.0, pool=2.0)) as httpx_client:
        config = ClientConfig(streaming=False, httpx_client=httpx_client)
        client = await create_client(agent=public_agent_card, client_config=config)

        message = new_text_message(text_query, role=Role.ROLE_USER)
        request = SendMessageRequest(message=message)

        response = ""
        async for chunk in client.send_message(request):
            # TODO: Figure out how to handle the response when streaming is False
            response = chunk.task.artifacts[0].parts[0].text

        await client.close()

    return response

class TestRagAgent:

    def test_advise_on_function(self):
        message = asyncio.run(send_message(text_query="What is the best way to name functions ?"))
        assert "conventions" in message.lower()
