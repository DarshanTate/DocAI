from datetime import datetime, timezone
from uuid import uuid4

from app.models.document import Document, DocumentStatus
from app.services.document_repository import DocumentRepository
from app.services.storage import FileStorageService


class DocumentService:
    def __init__(
        self,
        repository: DocumentRepository,
        storage: FileStorageService,
    ):
        self.repository = repository
        self.storage = storage

    def upload_document(
        self,
        filename: str,
        content: bytes,
        file_type: str,
    ) -> Document:

        document_id = uuid4()

        now = datetime.now(timezone.utc)

        storage_path = self.storage.save_file(
            document_id=document_id,
            filename=filename,
            content=content,
        )

        document = Document(
            id=document_id,
            filename=filename,
            original_filename=filename,
            file_type=file_type,
            file_size=len(content),
            storage_path=str(storage_path),
            status=DocumentStatus.UPLOADED,
            created_at=now,
            updated_at=now,
        )

        return self.repository.create(document)