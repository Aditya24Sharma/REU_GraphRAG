import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List


def text_chunking(
    text: str, chunk_size: int = 2500, chunk_overlap=200, seperators: List[str] = []
) -> List[str]:
    """
    Splits the text into multiple chunks to send to LLMs
    Args:
        text(str): text which has to be chunked into batches
        chunk_size(int): size of each chunk
        chunk_overlap(int): overlap between the chunks
        seperators(list[str]): seperators to seperate the text to get extract chunks
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap, separators=seperators
    )
    chunks: List[str] = splitter.split_text(text)
    return chunks


if __name__ == "__main__":
    filepath = os.path.abspath(
        "markdowns/Establishing flood thresholds for sea level rise impact communication.md"
    )
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()
        chunks = text_chunking(text=text)
