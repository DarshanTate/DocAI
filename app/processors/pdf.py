from pathlib import Path

from pypdf import PdfReader

from app.processors.base import BaseDocumentProcessor
from app.processors.types import DocumentElement, ParsedDocument

from app.processors.pdf_ocr import PDFOCRProcessor


class PDFProcessor(BaseDocumentProcessor):

    def can_process(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == ".pdf"

    def process(self, file_path: Path) -> ParsedDocument:
        reader = PdfReader(file_path)

        parsed_elements = []
        
        for page_number, page in enumerate(
            reader.pages,
            start=1,
        ):
        
            text = page.extract_text() or ""
        
            text = text.strip()
        
            if text:
                parsed_elements.append(
                    DocumentElement(
                        content=text,
                        content_type="text",
                        metadata={
                            "page": page_number,
                            "ocr": False,
                        },
                    )
                )
        
        if parsed_elements:
            return ParsedDocument(
                elements=parsed_elements
            )
        
        return PDFOCRProcessor().process(
            str(file_path)
        )