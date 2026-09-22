from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document


class DocumentRepository:

    def create(
        self,
        db: Session,
        document: Document,
    ) -> Document:

        db.add(document)
        db.commit()
        db.refresh(document)

        return document

    def get(
        self,
        db: Session,
        document_id: UUID,
    ) -> Document | None:

        statement = select(Document).where(
            Document.id == document_id
        )

        return db.scalar(statement)

    def list(
        self,
        db: Session,
    ) -> list[Document]:

        statement = select(Document).order_by(
            Document.created_at.desc()
        )

        return list(db.scalars(statement).all())

    def update(
        self,
        db: Session,
        document: Document,
    ) -> Document:

        db.commit()
        db.refresh(document)

        return document