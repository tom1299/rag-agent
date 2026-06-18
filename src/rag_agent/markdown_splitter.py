from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter

default_headers_to_split_on = [
    ("#", "Header 1"),
    ("##", "Header 2"),
    ("###", "Header 3"),
]

def split_markdown(text: str, headers_to_split_on: list[tuple[str, str]] = default_headers_to_split_on) -> list[Document]:
    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on)
    return markdown_splitter.split_text(text)


def split_markdown_folder(
    folder: Path,
    headers_to_split_on: list[tuple[str, str]] = default_headers_to_split_on,
) -> list[Document]:
    """Recursively find all .md files in folder and split each by headers.

    Args:
        folder:               Path to the folder to search.
        headers_to_split_on:  Header levels to split on.

    Returns:
        Combined list of Documents from all markdown files found.
    """
    documents = []
    for md_file in sorted(folder.rglob("*.md")):
        # TODO: Add metadata to documents (like path)
        text = md_file.read_text(encoding="utf-8")
        documents.extend(split_markdown(text, headers_to_split_on))
    return documents