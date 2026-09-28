from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.services.structured.tabular_qa_service import (
    TabularQAService,
)


class DocumentTabularService:

    def __init__(self):
        self.qa_service = TabularQAService()

    def answer(
        self,
        db: Session,
        document_id: UUID,
        question: str,
    ) -> str:

        statement = select(Document).where(
            Document.id == document_id
        )

        document = db.scalar(statement)

        if document is None:
            raise ValueError("Document not found.")

        return self.qa_service.answer(
            file_path=document.storage_path,
            question=question,
        )