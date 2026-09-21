from datetime import datetime, timezone
from uuid import uuid4

from app.models.job import JobStatus, ProcessingJob
from app.services.job_repository import JobRepository
from app.services.job_queue import JobQueue


class JobService:

    def __init__(
        self,
        repository: JobRepository,
        queue: JobQueue,
    ):
        self.repository = repository
        self.queue = queue

    def create_document_job(
        self,
        document_id,
    ) -> ProcessingJob:

        now = datetime.now(timezone.utc)

        job = ProcessingJob(
            id=uuid4(),
            document_id=document_id,
            status=JobStatus.QUEUED,
            created_at=now,
            updated_at=now,
        )

        self.repository.create(job)

        self.queue.enqueue_document_processing(
            str(document_id)
        )

        return job