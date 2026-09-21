from uuid import UUID

from app.models.document import Document


class DocumentRepository:
    def __init__(self):
        self._documents: dict[UUID, Document] = {}

    def create(self, document: Document) -> Document:
        self._documents[document.id] = document
        return document

    def get(self, document_id: UUID) -> Document | None:
        return self._documents.get(document_id)

    def list(self) -> list[Document]:
        return list(self._documents.values())