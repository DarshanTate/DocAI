from pathlib import Path
from uuid import UUID
import shutil

import boto3
from fastapi import UploadFile

from app.core.config import settings


class FileStorageService:

    def __init__(self):
        self.client = None

        if settings.storage_backend == "s3":
            self.client = boto3.client(
                "s3",
                endpoint_url=settings.s3_endpoint_url or None,
                aws_access_key_id=settings.s3_access_key,
                aws_secret_access_key=settings.s3_secret_key,
                region_name=settings.s3_region,
            )

    # ---------------------------------------------------------
    # SAVE FILE
    # ---------------------------------------------------------

    def save_file(
        self,
        file: UploadFile,
        document_id: UUID,
    ) -> tuple[str, int]:

        filename = Path(
            file.filename or "uploaded_file"
        ).name

        if settings.storage_backend == "s3":
            return self._save_s3(
                file=file,
                document_id=document_id,
                filename=filename,
            )

        return self._save_local(
            file=file,
            document_id=document_id,
            filename=filename,
        )

    # ---------------------------------------------------------
    # LOCAL STORAGE
    # ---------------------------------------------------------

    def _save_local(
        self,
        file: UploadFile,
        document_id: UUID,
        filename: str,
    ) -> tuple[str, int]:

        base_dir = Path("storage/documents")

        document_dir = (
            base_dir / str(document_id)
        )

        document_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

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

    # ---------------------------------------------------------
    # S3 STORAGE
    # ---------------------------------------------------------

    def _save_s3(
        self,
        file: UploadFile,
        document_id: UUID,
        filename: str,
    ) -> tuple[str, int]:

        object_key = (
            f"documents/{document_id}/{filename}"
        )

        # Determine file size without loading
        # the entire file into memory.
        current_position = file.file.tell()

        file.file.seek(0, 2)

        total_size = file.file.tell()

        file.file.seek(current_position)

        self.client.upload_fileobj(
            file.file,
            settings.s3_bucket,
            object_key,
        )

        return object_key, total_size

    # ---------------------------------------------------------
    # DOWNLOAD FILE
    # ---------------------------------------------------------

    def download_file(
        self,
        storage_path: str,
        destination: str,
    ) -> None:

        destination_path = Path(destination)

        destination_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if settings.storage_backend == "s3":

            if self.client is None:
                raise RuntimeError(
                    "S3 storage client is not initialized."
                )

            with destination_path.open("wb") as file:

                self.client.download_fileobj(
                    settings.s3_bucket,
                    storage_path,
                    file,
                )

            return

        # -----------------------------------------------------
        # LOCAL
        # -----------------------------------------------------

        source = Path(storage_path)

        if not source.exists():
            raise FileNotFoundError(
                f"File not found: {storage_path}"
            )

        with source.open("rb") as src:
            with destination_path.open("wb") as dst:

                shutil.copyfileobj(
                    src,
                    dst,
                    length=1024 * 1024,
                )

    # ---------------------------------------------------------
    # DELETE FILE
    # ---------------------------------------------------------

    def delete_file(
        self,
        storage_path: str,
    ) -> None:

        if settings.storage_backend == "s3":

            if self.client is None:
                raise RuntimeError(
                    "S3 storage client is not initialized."
                )

            self.client.delete_object(
                Bucket=settings.s3_bucket,
                Key=storage_path,
            )

            return

        # Local storage

        path = Path(storage_path)

        if path.exists():
            path.unlink()