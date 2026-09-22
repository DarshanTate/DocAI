from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.models.job import JobStatus, ProcessingJob
from app.services.job_queue import JobQueue
from app.services.job_repository import JobRepository


class JobService:

    def __init__(self):
        self.repository = JobRepository()
        self.queue = JobQueue()

    def create_job(
        self,
        db: Session,
        document_id: UUID,
    ) -> ProcessingJob:

        job = ProcessingJob(
            id=uuid4(),
            document_id=document_id,
            status=JobStatus.QUEUED,
            retry_count=0,
            max_retries=3,
        )

        job = self.repository.create(
            db=db,
            job=job,
        )

        self.queue.enqueue_document_processing(
            job_id=job.id,
            document_id=document_id,
        )

        return job

    def mark_processing(
        self,
        db: Session,
        job: ProcessingJob,
    ) -> ProcessingJob:

        job.status = JobStatus.PROCESSING
        job.started_at = datetime.now(timezone.utc)

        return self.repository.update(
            db=db,
            job=job,
        )

    def mark_completed(
        self,
        db: Session,
        job: ProcessingJob,
    ) -> ProcessingJob:

        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.now(timezone.utc)
        job.error_message = None

        return self.repository.update(
            db=db,
            job=job,
        )

    def mark_failed(
        self,
        db: Session,
        job: ProcessingJob,
        error_message: str,
    ) -> ProcessingJob:

        job.status = JobStatus.FAILED
        job.error_message = error_message

        return self.repository.update(
            db=db,
            job=job,
        )