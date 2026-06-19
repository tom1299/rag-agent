import tempfile
from pathlib import Path

from langchain_agent.agent import create_agent
from langchain_core.tools import tool
from .markdown_splitter import split_markdown_folder
from .vector_store import create_vector_store

from .git import clone_repo

def create_markdown_rag_agent(git_url: str, auth=None, model=None, system_prompt: str = None):
    documents_path = Path(tempfile.mkdtemp())
    clone_repo(git_url, dest=documents_path, auth=auth)
    markdown_documents = split_markdown_folder(documents_path)
    vector_store = create_vector_store(markdown_documents)

    # From  https://docs.langchain.com/oss/python/langchain/rag#rag-agents
    # TODO: Fix wrong imports in documentation
    @tool(response_format="content_and_artifact")
    def retrieve_context(query: str):
        """
        Retrieve relevant context for the given query from the vector store.

        :param query: The query for which to retrieve context.
        :return: Serialized context and the retrieved documents.
        """
        retrieved_docs = vector_store.similarity_search(query, k=2)
        serialized = "\n\n".join(
            f"Source: {doc.metadata}\nContent: {doc.page_content}" for doc in retrieved_docs
        )
        return serialized, retrieved_docs

    tools = [retrieve_context]
    agent = create_agent(model, tools=tools, system_prompt=system_prompt)

    return agent

