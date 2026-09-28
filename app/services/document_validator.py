from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings


class DocumentValidator:

    ALLOWED_MIME_TYPES = {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "text/csv",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "text/plain",
        "image/png",
        "image/jpeg",
        "image/webp",
    }

    def validate(self, file: UploadFile) -> None:

        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename is required.",
            )

        extension = (
            Path(file.filename)
            .suffix
            .lower()
            .lstrip(".")
        )

        if extension not in settings.allowed_extension_set:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: .{extension}",
            )

        if file.content_type not in self.ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported MIME type: {file.content_type}",
            )

        file.file.seek(0)

        total_size = 0

        while True:

            chunk = file.file.read(
                1024 * 1024
            )

            if not chunk:
                break

            total_size += len(chunk)

            if total_size > (
                settings.max_file_size_mb
                * 1024
                * 1024
            ):
                raise HTTPException(
                    status_code=413,
                    detail=(
                        f"File exceeds the "
                        f"{settings.max_file_size_mb} MB limit."
                    ),
                )

        if total_size == 0:
            raise HTTPException(
                status_code=400,
                detail="The uploaded file is empty.",
            )

        file.file.seek(0)