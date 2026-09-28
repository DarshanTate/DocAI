import json

from app.services.generation.llm_service import LLMService
from app.services.structured.tabular_service import TabularService


class TabularQAService:

    def __init__(self):
        self.tabular_service = TabularService()
        self.llm_service = LLMService()

    def answer(self, file_path: str, question: str) -> str:

        summary = self.tabular_service.column_summary(
            file_path
        )

        preview = self.tabular_service.preview(
            file_path,
            rows=20,
        )

        prompt = f"""
You are a data analysis assistant.

Answer the user's question using ONLY the provided
spreadsheet information.

Do not invent values.

If the information is insufficient, say so.

QUESTION:
{question}

COLUMN SUMMARY:
{json.dumps(summary, indent=2)}

DATA PREVIEW:
{json.dumps(preview, indent=2, default=str)}

ANSWER:
"""

        return self.llm_service.generate(prompt)