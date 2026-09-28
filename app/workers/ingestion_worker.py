import json
import logging
from uuid import UUID
from app.models.user import User
from app.db.database import SessionLocal
from app.db.redis import redis_client
from app.models.document import DocumentStatus
from app.models.job import JobStatus
from app.services.document_repository import DocumentRepository
from app.services.ingestion_service import IngestionService
from app.services.job_repository import JobRepository
from app.services.job_service import JobService
from app.services.job_queue import QUEUE_NAME

from app.services.embeddings.embedding_service import EmbeddingService
from app.services.retrieval.vector_store import VectorStore

logging.basicConfig(
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

document_repository = DocumentRepository()
job_repository = JobRepository()
job_service = JobService()
ingestion_service = IngestionService()

embedding_service = EmbeddingService()
vector_store = VectorStore()

vector_store.create_collection()

def process_job(payload: dict) -> None:

    job_id = UUID(payload["job_id"])
    document_id = UUID(payload["document_id"])

    db = SessionLocal()

    try:
        job = job_repository.get(
            db=db,
            job_id=job_id,
        )

        document = document_repository.get(
            db=db,
            document_id=document_id,
        )

        if job is None:
            logger.error("Job %s not found.", job_id)
            return

        if document is None:
            logger.error("Document %s not found.", document_id)
            return

        if job.status == JobStatus.COMPLETED:
            return

        job_service.mark_processing(
            db=db,
            job=job,
        )

        document.status = DocumentStatus.PROCESSING
        document_repository.update(
            db=db,
            document=document,
        )

        logger.info(
            "Processing document %s",
            document_id,
        )

        chunks = ingestion_service.process_and_chunk(
                document.storage_path,
        )

        logger.info(
            "Created %s chunks from document %s",
            len(chunks),
            document_id,
        )

        texts = [
            chunk.content
            for chunk in chunks
        ]

        embeddings = embedding_service.embed_texts(
            texts
        )

        vector_store.add_chunks(
            document_id=document_id,
            owner_id=document.owner_id,
            chunks=chunks,
            embeddings=embeddings,
        )

        logger.info(
            "Indexed %s chunks for document %s",
            len(chunks),
            document_id,
        )

        document.status = DocumentStatus.READY

        document_repository.update(
            db=db,
            document=document,
        )

        job_service.mark_completed(
            db=db,
            job=job,
        )

        logger.info(
            "Document %s completed.",
            document_id,
        )

    except Exception as exc:
        db.rollback()
        logger.exception(
            "Failed processing document %s",
            document_id,
        )

        job = job_repository.get(
            db=db,
            job_id=job_id,
        )

        document = document_repository.get(
            db=db,
            document_id=document_id,
        )

        if job is not None:
            job_service.mark_failed(
                db=db,
                job=job,
                error_message=str(exc),
            )

        if document is not None:
            document.status = DocumentStatus.FAILED

            document_repository.update(
                db=db,
                document=document,
            )

    finally:
        db.close()


def run_worker() -> None:

    logger.info(
        "DocAI ingestion worker started."
    )

    while True:

        result = redis_client.blpop(
            QUEUE_NAME,
            timeout=0,
        )

        if result is None:
            continue

        _, raw_job = result

        try:
            payload = json.loads(raw_job)
            process_job(payload)

        except Exception:
            logger.exception(
                "Invalid job received from Redis."
            )


if __name__ == "__main__":
    run_worker()