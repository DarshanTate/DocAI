from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.job import JobStatus


class JobResponse(BaseModel):
    id: UUID
    document_id: UUID
    status: JobStatus
    retry_count: int
    max_retries: int
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )