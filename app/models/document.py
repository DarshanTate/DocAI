from datetime import datetime
from enum import Enum
from uuid import UUID


class DocumentStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class Document:
    def __init__(
        self,
        id: UUID,
        filename: str,
        original_filename: str,
        file_type: str,
        file_size: int,
        storage_path: str,
        status: DocumentStatus,
        created_at: datetime,
        updated_at: datetime,
    ):
        self.id = id
        self.filename = filename
        self.original_filename = original_filename
        self.file_type = file_type
        self.file_size = file_size
        self.storage_path = storage_path
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at