from uuid import UUID
from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile

from fastapi import (
    APIRouter,
    Depends,
    File,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.document import (
    DocumentResponse,
    DocumentStatusResponse,
)
from app.services.document_service import (
    DocumentService,
)


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)

document_service = DocumentService()


@router.post(
    "/upload",
    response_model=list[DocumentResponse],
    status_code=status.HTTP_201_CREATED,
)
def upload_documents(
    files: Annotated[list[UploadFile], File(...)],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    results = []

    for file in files:
        document = document_service.upload_document(
            db=db,
            file=file,
            owner_id=current_user.id,
        )

        results.append(document)

    return results


@router.get(
    "/",
    response_model=list[DocumentResponse],
)
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    return document_service.list_documents(
        db=db,
        owner_id=current_user.id,
    )


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
)
def get_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    return document_service.get_document(
        db=db,
        document_id=document_id,
        owner_id=current_user.id,
    )


@router.get(
    "/{document_id}/status",
    response_model=DocumentStatusResponse,
)
def get_document_status(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    document_status = (
        document_service.get_document_status(
            db=db,
            document_id=document_id,
            owner_id=current_user.id,
        )
    )

    return DocumentStatusResponse(
        document_id=document_id,
        status=document_status,
    )