from fastapi import APIRouter, File, UploadFile

from app.schemas.document import DocumentResponse
from app.services.document_repository import DocumentRepository
from app.services.document_service import DocumentService
from app.services.storage import FileStorageService

from app.services.job_queue import JobQueue
from app.services.job_repository import JobRepository
from app.services.job_service import JobService


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)

job_repository = JobRepository()
job_queue = JobQueue()

job_service = JobService(
    repository=job_repository,
    queue=job_queue,
)

repository = DocumentRepository()
storage = FileStorageService()
document_service = DocumentService(
    repository=repository,
    storage=storage,
)


@router.post(
    "",
    response_model=DocumentResponse,
)
async def upload_document(
    file: UploadFile = File(...),
):
    content = await file.read()

    document = document_service.upload_document(
        filename=file.filename or "unknown",
        content=content,
        file_type=file.content_type or "application/octet-stream",
    )

    job = job_service.create_document_job(
    document_id=document.id
)

    return DocumentResponse(
        id=document.id,
        filename=document.filename,
        original_filename=document.original_filename,
        file_type=document.file_type,
        file_size=document.file_size,
        status=document.status,
        created_at=document.created_at,
        updated_at=document.updated_at,
    )

@router.get(
    "",
    response_model=list[DocumentResponse],
)
async def list_documents():
    documents = repository.list()

    return [
        DocumentResponse(
            id=document.id,
            filename=document.filename,
            original_filename=document.original_filename,
            file_type=document.file_type,
            file_size=document.file_size,
            status=document.status,
            created_at=document.created_at,
            updated_at=document.updated_at,
        )
        for document in documents
    ]