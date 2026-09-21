from datetime import datetime
from enum import Enum
from uuid import UUID


class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ProcessingJob:

    def __init__(
        self,
        id: UUID,
        document_id: UUID,
        status: JobStatus,
        created_at: datetime,
        updated_at: datetime,
        error_message: str | None = None,
    ):
        self.id = id
        self.document_id = document_id
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at
        self.error_message = error_message