from pathlib import Path
import csv

from app.processors.base import BaseDocumentProcessor
from app.processors.types import DocumentElement, ParsedDocument


class CSVProcessor(BaseDocumentProcessor):

    def can_process(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == ".csv"

    def process(self, file_path: Path) -> ParsedDocument:
        elements = []

        with file_path.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as file:
            reader = csv.reader(file)

            rows = list(reader)

        if rows:
            headers = rows[0]

            lines = [
                " | ".join(headers),
                " | ".join(["---"] * len(headers)),
            ]

            for row in rows[1:]:
                lines.append(" | ".join(row))

            elements.append(
                DocumentElement(
                    content="\n".join(lines),
                    content_type="table",
                    metadata={},
                )
            )

        return ParsedDocument(
            elements=elements,
            metadata={
                "file_type": "csv",
            },
        )