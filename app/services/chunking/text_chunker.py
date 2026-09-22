from dataclasses import dataclass
from typing import Any

from app.processors.types import DocumentElement


@dataclass
class TextChunk:
    content: str
    metadata: dict[str, Any]


class TextChunker:
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):
        if chunk_overlap >= chunk_size:
            raise ValueError(
                "chunk_overlap must be smaller than chunk_size"
            )

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_elements(
        self,
        elements: list[DocumentElement],
    ) -> list[TextChunk]:

        chunks: list[TextChunk] = []

        for element in elements:
            text = element.content.strip()

            if not text:
                continue

            chunks.extend(
                self._chunk_text(
                    text=text,
                    metadata=element.metadata,
                    content_type=element.content_type,
                )
            )

        return chunks

    def _chunk_text(
        self,
        text: str,
        metadata: dict[str, Any],
        content_type: str,
    ) -> list[TextChunk]:

        chunks: list[TextChunk] = []

        start = 0
        text_length = len(text)

        while start < text_length:
            end = min(
                start + self.chunk_size,
                text_length,
            )

            chunk_text = text[start:end].strip()

            if chunk_text:
                chunk_metadata = {
                    **metadata,
                    "content_type": content_type,
                    "start_char": start,
                    "end_char": end,
                }

                chunks.append(
                    TextChunk(
                        content=chunk_text,
                        metadata=chunk_metadata,
                    )
                )

            if end >= text_length:
                break

            start = end - self.chunk_overlap

        return chunks