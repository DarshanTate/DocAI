from pathlib import Path

import pytesseract
from pdf2image import convert_from_path

from app.processors.types import (
    DocumentElement,
    ParsedDocument,
)


class PDFOCRProcessor:

    def process(self, file_path: str) -> ParsedDocument:

        pages = convert_from_path(
            file_path,
            dpi=200,
        )

        elements = []

        for page_number, image in enumerate(
            pages,
            start=1,
        ):

            text = pytesseract.image_to_string(
                image
            ).strip()

            if text:

                elements.append(
                    DocumentElement(
                        content=text,
                        content_type="ocr_text",
                        metadata={
                            "page": page_number,
                            "ocr": True,
                        },
                    )
                )

        return ParsedDocument(
            elements=elements,
            metadata={
                "ocr": True,
                "source": Path(file_path).name,
            },
        )