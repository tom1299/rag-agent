from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore

from langchain_openai import OpenAIEmbeddings

def create_vector_store(documents: list[Document]) -> InMemoryVectorStore:
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
    vector_store = InMemoryVectorStore(embeddings)
    vector_store.add_documents(documents)
    return vector_store