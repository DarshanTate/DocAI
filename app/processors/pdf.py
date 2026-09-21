from pathlib import Path

from pypdf import PdfReader

from app.processors.base import BaseDocumentProcessor
from app.processors.types import DocumentElement, ParsedDocument


class PDFProcessor(BaseDocumentProcessor):

    def can_process(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == ".pdf"

    def process(self, file_path: Path) -> ParsedDocument:
        reader = PdfReader(file_path)

        elements = []

        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""

            if not text.strip():
                continue

            elements.append(
                DocumentElement(
                    content=text,
                    content_type="text",
                    metadata={
                        "page": page_number,
                    },
                )
            )

        return ParsedDocument(
            elements=elements,
            metadata={
                "file_type": "pdf",
                "page_count": len(reader.pages),
            },
        )