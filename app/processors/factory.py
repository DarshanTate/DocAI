from pathlib import Path

from app.processors.base import BaseDocumentProcessor
from app.processors.csv import CSVProcessor
from app.processors.docx import DOCXProcessor
from app.processors.pdf import PDFProcessor
from app.processors.pptx import PPTXProcessor
from app.processors.txt import TXTProcessor
from app.processors.xlsx import XLSXProcessor


class DocumentProcessorFactory:

    def __init__(self):
        self.processors: list[BaseDocumentProcessor] = [
            PDFProcessor(),
            DOCXProcessor(),
            XLSXProcessor(),
            CSVProcessor(),
            PPTXProcessor(),
            TXTProcessor(),
        ]

    def get_processor(
        self,
        file_path: Path,
    ) -> BaseDocumentProcessor:

        for processor in self.processors:
            if processor.can_process(file_path):
                return processor

        raise ValueError(
            f"Unsupported document type: {file_path.suffix}"
        )