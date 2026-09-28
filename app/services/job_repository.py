from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.job import ProcessingJob


class JobRepository:

    def create(
        self,
        db: Session,
        job: ProcessingJob,
    ) -> ProcessingJob:

        db.add(job)
        db.commit()
        db.refresh(job)

        return job

    def get(
        self,
        db: Session,
        job_id: UUID,
    ) -> ProcessingJob | None:

        statement = select(
            ProcessingJob
        ).where(
            ProcessingJob.id == job_id
        )

        return db.scalar(statement)

    def get_for_owner(
        self,
        db: Session,
        job_id: UUID,
        owner_id: UUID,
    ) -> ProcessingJob | None:

        statement = (
            select(ProcessingJob)
            .join(
                Document,
                ProcessingJob.document_id == Document.id,
            )
            .where(
                ProcessingJob.id == job_id,
                Document.owner_id == owner_id,
            )
        )

        return db.scalar(statement)

    def get_by_document_id(
        self,
        db: Session,
        document_id: UUID,
    ) -> ProcessingJob | None:

        statement = (
            select(ProcessingJob)
            .where(
                ProcessingJob.document_id == document_id
            )
            .order_by(
                ProcessingJob.created_at.desc()
            )
        )

        return db.scalar(statement)

    def update(
        self,
        db: Session,
        job: ProcessingJob,
    ) -> ProcessingJob:

        db.commit()
        db.refresh(job)

        return job