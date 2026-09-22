from pathlib import Path
from uuid import UUID

from fastapi import UploadFile


class FileStorageService:
    BASE_DIR = Path("storage/documents")

    def __init__(self):
        self.BASE_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

    def save_file(
        self,
        file: UploadFile,
        document_id: UUID,
    ) -> tuple[str, int]:

        document_dir = self.BASE_DIR / str(document_id)
        document_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        filename = Path(file.filename or "uploaded_file").name
        file_path = document_dir / filename

        total_size = 0

        with file_path.open("wb") as buffer:
            while True:
                chunk = file.file.read(1024 * 1024)

                if not chunk:
                    break

                buffer.write(chunk)
                total_size += len(chunk)

        return str(file_path), total_size