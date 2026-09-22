from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings


class DocumentValidator:

    def validate(self, file: UploadFile) -> None:
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename is required.",
            )

        extension = Path(file.filename).suffix.lower().lstrip(".")

        if extension not in settings.allowed_extension_set:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Unsupported file type '.{extension}'. "
                    f"Allowed types: "
                    f"{', '.join(sorted(settings.allowed_extension_set))}"
                ),
            )

        if file.content_type:
            allowed_mime_types = {
                "application/pdf",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "text/csv",
                "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                "text/plain",
            }

            if file.content_type not in allowed_mime_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported MIME type: {file.content_type}",
                )

        file.file.seek(0)

        first_chunk = file.file.read(1024)

        if not first_chunk:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The uploaded file is empty.",
            )

        file.file.seek(0)