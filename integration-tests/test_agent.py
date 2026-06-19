import os

import unittest

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import ToolMessage, AIMessage

from rag_agent.git import AuthMethod, GitAuth
from rag_agent.agent import create_markdown_rag_agent

load_dotenv()

class TestRagMarkdownAgent(unittest.TestCase):

    def setUp(self):
        self.token = os.getenv("IT_TEST_GIT_TOKEN")
        self.username = os.getenv("IT_TEST_GIT_USER")
        if not self.token:
            self.skipTest("GIT_TOKEN not set — skipping private repo tests")

    def test_code_advisor_rag_agent(self):
        auth = GitAuth(
            method=AuthMethod.BASIC,
            username=self.username,
            password=self.token,
        )
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
        agent = create_markdown_rag_agent(os.getenv("IT_TEST_REPO_URL"),
                    model=model, system_prompt=system_prompt, auth=auth)
        query = """
        Apply code guidelines to the following function. Include refactored code and citation
        of the relevant documents in your answer.:
        ```python
        def O(O0,OO):
         OOO=O0+OO
         return OOO
        ```
        """
        response = agent.invoke({"messages": [{"role": "user", "content": query}]})
        tool_invocation: AIMessage = response["messages"][1]
        tool_response: ToolMessage = response["messages"][2]
        final_response: AIMessage = response["messages"][3]

        assert tool_invocation.tool_calls[0]["name"] == 'retrieve_context'

        assert tool_response.artifact[0].metadata['Header 1'] == 'Conventions and Documentation'

        assert "Conventions and Documentation" in final_response.text

        print(response)


