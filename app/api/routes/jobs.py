from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
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
):
    job = job_repository.get(
        db=db,
        job_id=job_id,
    )

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found.",
        )

    return job