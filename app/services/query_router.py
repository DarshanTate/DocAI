from pathlib import Path


class QueryRouter:

    STRUCTURED_EXTENSIONS = {".csv", ".xlsx"}

    STRUCTURED_KEYWORDS = {
        "average",
        "mean",
        "sum",
        "total",
        "maximum",
        "minimum",
        "max",
        "min",
        "count",
        "how many",
        "percentage",
        "percent",
        "highest",
        "lowest",
        "column",
        "row",
    }

    def route(self, question: str, documents: list) -> str:
        question_lower = question.lower()

        has_structured_document = any(
            Path(document.storage_path).suffix.lower()
            in self.STRUCTURED_EXTENSIONS
            for document in documents
        )

        if (
            has_structured_document
            and any(
                keyword in question_lower
                for keyword in self.STRUCTURED_KEYWORDS
            )
        ):
            return "structured"

        return "rag"