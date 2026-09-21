from pathlib import Path
from uuid import UUID


class FileStorageService:
    def __init__(self, base_path: str = "storage/documents"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def get_document_path(
        self,
        document_id: UUID,
        filename: str,
    ) -> Path:
        document_directory = self.base_path / str(document_id)
        document_directory.mkdir(parents=True, exist_ok=True)

        return document_directory / filename

    def save_file(
        self,
        document_id: UUID,
        filename: str,
        content: bytes,
    ) -> Path:
        path = self.get_document_path(document_id, filename)

        path.write_bytes(content)

        return path