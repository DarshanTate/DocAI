from pathlib import Path

from app.processors.base import BaseDocumentProcessor
from app.processors.types import (
    DocumentElement,
    ParsedDocument,
)
from app.processors.ocr import OCRProcessor


class ImageProcessor(BaseDocumentProcessor):

    SUPPORTED_EXTENSIONS = {
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
    }

    def __init__(self):
        self.ocr = OCRProcessor()

    def can_process(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS

    def process(self, file_path: Path) -> ParsedDocument:

        text = self.ocr.process_image(
            str(file_path)
        )

        if not text:
            return ParsedDocument(elements=[])

        element = DocumentElement(
            content=text,
            content_type="ocr_text",
            metadata={
                "source": file_path.name,
                "ocr": True,
            },
        )

        return ParsedDocument(
            elements=[element],
            metadata={
                "ocr": True,
            },
        )