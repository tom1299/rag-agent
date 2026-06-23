from pathlib import Path

from a2a.helpers import (
    get_message_text,
    new_task_from_user_message,
    new_text_message,
    new_text_part,
)
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types.a2a_pb2 import TaskState
from langchain_core.messages.base import BaseMessage

from rag_agent.agent import create_markdown_rag_agent, create_markdown_rag_agent_from_path


class RagAgentExecutor(AgentExecutor):

    def __init__(self, agent) -> None:
        self._agent = agent

    @classmethod
    def from_path(cls, document_path: Path, model=None, system_prompt: str = None) -> 'RagAgentExecutor':
        return cls(create_markdown_rag_agent_from_path(document_path, model=model, system_prompt=system_prompt))

    @classmethod
    def from_git_url(cls, git_url: str, auth=None, model=None, system_prompt: str = None) -> 'RagAgentExecutor':
        return cls(create_markdown_rag_agent(git_url, auth=auth, model=model, system_prompt=system_prompt))

    async def invoke(self, user_request: str) -> str:
        result = self._agent.invoke(
            {"messages": [{"role": "user", "content": user_request}]},
            stream_mode="values"
        )

        messages = result["messages"]
        final_response: BaseMessage = messages[len(messages) - 1]

        return final_response.text

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:

        if context.current_task:
            task = context.current_task
        else:
            task = new_task_from_user_message(context.message)
            await event_queue.enqueue_event(task)

        task_updater = TaskUpdater(
            event_queue=event_queue, task_id=task.id, context_id=task.context_id
        )
        await task_updater.update_status(
            state=TaskState.TASK_STATE_WORKING,
            message=new_text_message('Processing request...'),
        )

        query = get_message_text(context.message)
        if query:
            result = await self.invoke(user_request=query)
        else:
            result = 'No text input is provided!'

        await task_updater.add_artifact(parts=[new_text_part(text=result, media_type='text/plain')])
        print('Result: ', result)

        await task_updater.update_status(
            state=TaskState.TASK_STATE_COMPLETED,
            message=new_text_message('Request is completed!'),
        )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError('Cancel is not supported.')
