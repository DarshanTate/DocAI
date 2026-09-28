from uuid import UUID, uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.models.document import (
    Document,
    DocumentStatus,
)
from app.services.document_repository import (
    DocumentRepository,
)
from app.services.document_validator import (
    DocumentValidator,
)
from app.services.job_service import JobService
from app.services.storage import FileStorageService


class DocumentService:

    def __init__(self):

        self.repository = DocumentRepository()
        self.storage = FileStorageService()
        self.validator = DocumentValidator()
        self.job_service = JobService()

    def upload_document(
        self,
        db: Session,
        file: UploadFile,
        owner_id: UUID,
    ) -> Document:

        self.validator.validate(file)

        document_id = uuid4()

        storage_path, file_size = (
            self.storage.save_file(
                file=file,
                document_id=document_id,
            )
        )

        document = Document(
            id=document_id,
            owner_id=owner_id,
            filename=file.filename,
            original_filename=file.filename,
            file_type=(
                file.content_type
                or "application/octet-stream"
            ),
            file_size=file_size,
            storage_path=storage_path,
            status=DocumentStatus.UPLOADED,
        )

        document = self.repository.create(
            db=db,
            document=document,
        )

        self.job_service.create_job(
            db=db,
            document_id=document.id,
        )

        return document

    def get_document(
        self,
        db: Session,
        document_id: UUID,
        owner_id: UUID,
    ) -> Document:

        document = self.repository.get_for_owner(
            db=db,
            document_id=document_id,
            owner_id=owner_id,
        )

        if document is None:

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found.",
            )

        return document

    def list_documents(
        self,
        db: Session,
        owner_id: UUID,
    ) -> list[Document]:

        return self.repository.list(
            db=db,
            owner_id=owner_id,
        )

    def get_document_status(
        self,
        db: Session,
        document_id: UUID,
        owner_id: UUID,
    ):

        document = self.get_document(
            db=db,
            document_id=document_id,
            owner_id=owner_id,
        )

        return document.status