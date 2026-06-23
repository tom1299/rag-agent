import sys
from pathlib import Path

from dotenv import load_dotenv

import uvicorn
import logging

from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import (
    create_agent_card_routes,
    create_jsonrpc_routes,
)
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentSkill,
)
from langchain.chat_models import init_chat_model

from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from rag_agent.a2a.agent_executor import RagAgentExecutor

logger = logging.getLogger("http_log")
logging.basicConfig(level=logging.DEBUG, format="%(message)s")


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        body = await request.body()
        logger.info(f">>> {request.method} {request.url}\n{body.decode(errors='replace')}")
        response = await call_next(request)

        # Buffer the response body to log it
        chunks = []
        async for chunk in response.body_iterator:
            chunks.append(chunk)
        response_body = b"".join(chunks)
        logger.info(f"<<< {response.status_code}\n{response_body.decode(errors='replace')}")

        from starlette.responses import Response
        return Response(
            content=response_body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
        )


def start_agent(document_path: Path, model=None, system_prompt: str = None):
    skill = AgentSkill(
        id='rag_agent',
        name='Rag Agent',
        description='A basic rag agent that provides advices based on documents',
        input_modes=['text/plain'],
        output_modes=['text/plain'],
        tags=['a2a', 'rag-agent'],
        examples=['Apply coding style guides to this function'],
    )

    public_agent_card = AgentCard(
        name='Rag Agent',
        description='A basic rag agent that provides advices based on documents',
        version='0.0.1',
        default_input_modes=['text/plain'],
        default_output_modes=['text/plain'],
        capabilities=AgentCapabilities(streaming=False, extended_agent_card=False),
        supported_interfaces=[
            AgentInterface(
                protocol_binding='JSONRPC',
                url='http://127.0.0.1:9998',  # URL ? http://localhost:4000/a2a/jsonrpc
            )
        ],
        skills=[skill]
    )

    request_handler = DefaultRequestHandler(
        agent_executor=RagAgentExecutor.from_path(document_path, model=model, system_prompt=system_prompt),
        task_store=InMemoryTaskStore(),
        agent_card=public_agent_card,
    )

    routes = []
    routes.extend(create_agent_card_routes(public_agent_card))
    routes.extend(create_jsonrpc_routes(request_handler, '/'))

    app = Starlette(routes=routes)
    app.add_middleware(LoggingMiddleware)

    uvicorn.run(app, host=None, port=9998, log_level="trace")

def start_server(document_path: Path):
    load_dotenv()
    model = init_chat_model("gpt-4.1")
    system_prompt = """
        You are a helpful assistant that provides code reviews for Python code.
        Your responses must be inline with custom code guidelines.
        Always use the tool retrieve_context to retrieve relevant context for your answer.
        Do not pass the code to the tool retrieve_context.
        Instead, formulate a query for the tool retrieve_context that describes what kind of information you need to apply the code guidelines to the code.
        For example if the source code is a function, the query could be:
        ```
        What should function parameters be named?
        What should variables be named?
        ```
        Always strictly apply the guidelines retrieved from retrieve_context to your answer.
        The guidelines must always be the basis for your answer.
        Always include the most relevant document from the retrieved context as a citation in your answer.
    """
    start_agent(document_path, model, system_prompt)

if __name__ == '__main__':
    document_path = Path(sys.argv[1])
    start_server(document_path)

