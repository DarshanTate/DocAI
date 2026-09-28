import re
from dataclasses import dataclass

from app.processors.types import DocumentElement


@dataclass
class TextChunk:
    content: str
    metadata: dict


class TextChunker:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 150):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_elements(
        self,
        elements: list[DocumentElement],
    ) -> list[TextChunk]:

        chunks = []

        for element in elements:
            text = self._normalize_text(element.content)

            if not text:
                continue

            paragraphs = self._split_into_paragraphs(text)

            current_parts = []
            current_length = 0
            chunk_index = 0

            for paragraph in paragraphs:

                # Large paragraph → split into sentences.
                if len(paragraph) > self.chunk_size:
                    units = self._split_into_sentences(paragraph)
                else:
                    units = [paragraph]

                for unit in units:
                    unit = unit.strip()

                    if not unit:
                        continue

                    unit_length = len(unit)

                    # Current chunk would become too large.
                    if (
                        current_parts
                        and current_length + unit_length + 1
                        > self.chunk_size
                    ):
                        chunk_text = "\n\n".join(current_parts)

                        chunks.append(
                            self._create_chunk(
                                element,
                                chunk_text,
                                chunk_index,
                            )
                        )

                        chunk_index += 1

                        # Keep overlap from the previous chunk.
                        overlap = self._get_overlap(current_parts)

                        current_parts = [overlap] if overlap else []
                        current_length = len(overlap)

                    current_parts.append(unit)
                    current_length += unit_length + 1

            # Add remaining text.
            if current_parts:
                chunk_text = "\n\n".join(current_parts)

                chunks.append(
                    self._create_chunk(
                        element,
                        chunk_text,
                        chunk_index,
                    )
                )

        return chunks

    def _normalize_text(self, text: str) -> str:
        text = text.replace("\r\n", "\n")
        text = text.replace("\r", "\n")

        # Normalize spaces while keeping paragraph boundaries.
        text = re.sub(r"[ \t]+", " ", text)

        # Remove excessive blank lines.
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()

    def _split_into_paragraphs(self, text: str) -> list[str]:
        paragraphs = re.split(r"\n\s*\n", text)

        return [
            paragraph.strip()
            for paragraph in paragraphs
            if paragraph.strip()
        ]

    def _split_into_sentences(self, text: str) -> list[str]:
        sentences = re.split(
            r"(?<=[.!?])\s+",
            text,
        )

        return [
            sentence.strip()
            for sentence in sentences
            if sentence.strip()
        ]

    def _get_overlap(self, parts: list[str]) -> str:
        if not parts:
            return ""

        last_part = parts[-1]

        if len(last_part) <= self.chunk_overlap:
            return last_part

        return last_part[-self.chunk_overlap:]

    def _create_chunk(
        self,
        element: DocumentElement,
        content: str,
        chunk_index: int,
    ) -> TextChunk:

        metadata = dict(element.metadata or {})

        metadata["chunk_index"] = chunk_index
        metadata["chunking_strategy"] = "structure_aware"

        return TextChunk(
            content=content,
            metadata=metadata,
        )