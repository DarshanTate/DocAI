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

    # ---------------------------------------------------------
    # Internal lookup
    # Used by background worker
    # ---------------------------------------------------------

    def get(
        self,
        db: Session,
        document_id: UUID,
    ) -> Document | None:

        statement = select(Document).where(
            Document.id == document_id
        )

        return db.scalar(statement)

    # ---------------------------------------------------------
    # Authenticated lookup
    # Used by API
    # ---------------------------------------------------------

    def get_for_owner(
        self,
        db: Session,
        document_id: UUID,
        owner_id: UUID,
    ) -> Document | None:

        statement = select(Document).where(
            Document.id == document_id,
            Document.owner_id == owner_id,
        )

        return db.scalar(statement)

    # ---------------------------------------------------------
    # List user's documents
    # ---------------------------------------------------------

    def list(
        self,
        db: Session,
        owner_id: UUID,
    ) -> list[Document]:

        statement = (
            select(Document)
            .where(Document.owner_id == owner_id)
            .order_by(Document.created_at.desc())
        )

        return list(
            db.scalars(statement).all()
        )

    # ---------------------------------------------------------
    # Update
    # ---------------------------------------------------------

    def update(
        self,
        db: Session,
        document: Document,
    ) -> Document:

        db.commit()
        db.refresh(document)

        return document