from app.processors.types import DocumentElement
from app.services.chunking.text_chunker import TextChunker


def test_chunker_creates_chunks():

    element = DocumentElement(
        content="A" * 2500,
        content_type="text",
        metadata={
            "page": 1,
        },
    )

    chunker = TextChunker(
        chunk_size=1000,
        chunk_overlap=200,
    )

    chunks = chunker.chunk_elements(
        [element]
    )

    assert len(chunks) == 3
    assert chunks[0].metadata["page"] == 1