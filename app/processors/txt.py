from pathlib import Path

from app.processors.base import BaseDocumentProcessor
from app.processors.types import DocumentElement, ParsedDocument


class TXTProcessor(BaseDocumentProcessor):

    def can_process(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == ".txt"

    def process(self, file_path: Path) -> ParsedDocument:
        content = file_path.read_text(
            encoding="utf-8",
            errors="replace",
        )

        elements = []

        if content.strip():
            elements.append(
                DocumentElement(
                    content=content,
                    content_type="text",
                    metadata={},
                )
            )

        return ParsedDocument(
            elements=elements,
            metadata={
                "file_type": "txt",
            },
        )