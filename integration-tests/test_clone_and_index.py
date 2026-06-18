import os
import tempfile
import unittest
from pathlib import Path

from dotenv import load_dotenv

from rag_agent.git import AuthMethod, GitAuth, GIT_TRACE_VARS, clone_repo
from rag_agent.markdown_splitter import split_markdown_folder
from rag_agent.vector_store import create_vector_store

load_dotenv()

class TestCloneAndIndex(unittest.TestCase):

    def setUp(self):
        self.token = os.getenv("IT_TEST_GIT_TOKEN")
        self.username = os.getenv("IT_TEST_GIT_USER")
        if not self.token:
            self.skipTest("GIT_TOKEN not set — skipping private repo tests")

    def test_clone_and_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "it-test-repo"
            auth = GitAuth(
                method=AuthMethod.BASIC,
                username=self.username,
                password=self.token,
            )
            clone_repo(url=os.getenv("IT_TEST_REPO_URL"), dest=dest, auth=auth, trace_vars=GIT_TRACE_VARS)
            documents = split_markdown_folder(dest)
            vector_store = create_vector_store(documents)

            results = vector_store.similarity_search_with_score(
                "Why is (automated) Software Testing Important?"
            )

            for doc, score in results:
                print(doc)
                print(f"Score: {score}")
                print("==========")
