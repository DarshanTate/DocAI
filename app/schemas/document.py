from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.document import DocumentStatus


class DocumentResponse(BaseModel):
    id: UUID
    filename: str
    original_filename: str
    file_type: str
    file_size: int
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class DocumentStatusResponse(BaseModel):
    document_id: UUID
    status: DocumentStatus