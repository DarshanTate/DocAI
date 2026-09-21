from uuid import UUID

from app.models.job import ProcessingJob


class JobRepository:

    def __init__(self):
        self._jobs: dict[UUID, ProcessingJob] = {}

    def create(self, job: ProcessingJob) -> ProcessingJob:
        self._jobs[job.id] = job
        return job

    def get(self, job_id: UUID) -> ProcessingJob | None:
        return self._jobs.get(job_id)

    def update(self, job: ProcessingJob) -> ProcessingJob:
        self._jobs[job.id] = job
        return job