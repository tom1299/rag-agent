import unittest
from pathlib import Path

from rag_agent.markdown_splitter import split_markdown, split_markdown_folder

DATA_DIR = Path(__file__).parent / "data"
MD_FILE_COUNT = len(list(DATA_DIR.rglob("*.md")))

MARKDOWN = (
    "# Foo\n\n"
    "## Bar\n\n"
    "Hi this is Jim\n\n"
    "Hi this is Joe\n\n"
    "### Boo \n\n"
    " Hi this is Lance \n\n"
    "## Baz\n\n"
    " Hi this is Molly"
)


class TestSplitMarkdownDefault(unittest.TestCase):
    """Tests for split_markdown using the default headers (#, ##, ###)."""

    def setUp(self):
        self.docs = split_markdown(MARKDOWN)

    def test_produces_three_chunks(self):
        self.assertEqual(len(self.docs), 3)

    def test_first_chunk_content(self):
        self.assertIn("Hi this is Jim", self.docs[0].page_content)
        self.assertIn("Hi this is Joe", self.docs[0].page_content)

    def test_first_chunk_metadata(self):
        self.assertEqual(self.docs[0].metadata["Header 1"], "Foo")
        self.assertEqual(self.docs[0].metadata["Header 2"], "Bar")
        self.assertNotIn("Header 3", self.docs[0].metadata)

    def test_second_chunk_content(self):
        self.assertIn("Hi this is Lance", self.docs[1].page_content)

    def test_second_chunk_metadata(self):
        self.assertEqual(self.docs[1].metadata["Header 1"], "Foo")
        self.assertEqual(self.docs[1].metadata["Header 2"], "Bar")
        self.assertEqual(self.docs[1].metadata["Header 3"], "Boo")

    def test_third_chunk_content(self):
        self.assertIn("Hi this is Molly", self.docs[2].page_content)

    def test_third_chunk_metadata(self):
        self.assertEqual(self.docs[2].metadata["Header 1"], "Foo")
        self.assertEqual(self.docs[2].metadata["Header 2"], "Baz")
        self.assertNotIn("Header 3", self.docs[2].metadata)


class TestSplitMarkdownCustomHeaders(unittest.TestCase):
    """Tests for split_markdown with a custom headers_to_split_on."""

    def test_top_level_only_produces_one_chunk(self):
        docs = split_markdown(MARKDOWN, headers_to_split_on=[("#", "Header 1")])
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0].metadata["Header 1"], "Foo")

    def test_custom_header_names(self):
        docs = split_markdown(
            MARKDOWN,
            headers_to_split_on=[("#", "H1"), ("##", "H2")],
        )
        self.assertIn("H1", docs[0].metadata)
        self.assertIn("H2", docs[0].metadata)


class TestSplitMarkdownFolder(unittest.TestCase):
    """Tests for split_markdown_folder using nested sample data."""

    def setUp(self):
        self.docs = split_markdown_folder(DATA_DIR)

    def test_returns_at_least_one_document_per_file(self):
        # TODO: Not really verifies that all documents have been split. Alter mds and test to enhance test.
        self.assertGreaterEqual(len(self.docs), MD_FILE_COUNT)

    def test_all_documents_have_content(self):
        for doc in self.docs:
            self.assertTrue(doc.page_content.strip())
