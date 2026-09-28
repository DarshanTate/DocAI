from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.job import JobResponse
from app.services.job_repository import JobRepository


router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"],
)

job_repository = JobRepository()


@router.get(
    "/{job_id}",
    response_model=JobResponse,
)
def get_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    job = job_repository.get_for_owner(
        db=db,
        job_id=job_id,
        owner_id=current_user.id,
    )

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found.",
        )

    return job