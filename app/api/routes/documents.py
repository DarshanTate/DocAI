from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.document import (
    DocumentResponse,
    DocumentStatusResponse,
)
from app.services.document_service import DocumentService


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)

document_service = DocumentService()


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    return document_service.upload_document(
        db=db,
        file=file,
    )


@router.get(
    "/",
    response_model=list[DocumentResponse],
)
def list_documents(
    db: Session = Depends(get_db),
):
    return document_service.list_documents(
        db=db,
    )


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
)
def get_document(
    document_id: UUID,
    db: Session = Depends(get_db),
):
    return document_service.get_document(
        db=db,
        document_id=document_id,
    )


@router.get(
    "/{document_id}/status",
    response_model=DocumentStatusResponse,
)
def get_document_status(
    document_id: UUID,
    db: Session = Depends(get_db),
):
    document_status = document_service.get_document_status(
        db=db,
        document_id=document_id,
    )

    return DocumentStatusResponse(
        document_id=document_id,
        status=document_status,
    )