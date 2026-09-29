import json
import logging
import tempfile
from pathlib import Path
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
from app.services.storage import FileStorageService


# ---------------------------------------------------------
# Logging
# ---------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# Services
# ---------------------------------------------------------

document_repository = DocumentRepository()
job_repository = JobRepository()
job_service = JobService()
ingestion_service = IngestionService()
storage_service = FileStorageService()

embedding_service = EmbeddingService()
vector_store = VectorStore()

vector_store.create_collection()


# ---------------------------------------------------------
# Process Job
# ---------------------------------------------------------

def process_job(payload: dict) -> None:

    job_id = UUID(
        payload["job_id"]
    )

    document_id = UUID(
        payload["document_id"]
    )

    db = SessionLocal()

    try:

        # -------------------------------------------------
        # Get job
        # -------------------------------------------------

        job = job_repository.get(
            db=db,
            job_id=job_id,
        )

        # -------------------------------------------------
        # Get document
        # -------------------------------------------------

        document = document_repository.get(
            db=db,
            document_id=document_id,
        )

        if job is None:

            logger.error(
                "Job %s not found.",
                job_id,
            )

            return

        if document is None:

            logger.error(
                "Document %s not found.",
                document_id,
            )

            return

        # -------------------------------------------------
        # Prevent duplicate processing
        # -------------------------------------------------

        if job.status == JobStatus.COMPLETED:

            logger.info(
                "Job %s is already completed.",
                job_id,
            )

            return

        # -------------------------------------------------
        # Mark processing
        # -------------------------------------------------

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

        # -------------------------------------------------
        # Download document to temporary directory
        # -------------------------------------------------

        with tempfile.TemporaryDirectory() as temp_dir:

            filename = Path(
                document.storage_path
            ).name

            temp_path = (
                Path(temp_dir) / filename
            )

            storage_service.download_file(
                storage_path=document.storage_path,
                destination=str(temp_path),
            )

            logger.info(
                "Downloaded document %s to temporary path %s",
                document_id,
                temp_path,
            )

            # -------------------------------------------------
            # Parse + chunk document
            # -------------------------------------------------

            chunks = ingestion_service.process_and_chunk(
                str(temp_path),
            )

        logger.info(
            "Created %s chunks from document %s",
            len(chunks),
            document_id,
        )

        # -------------------------------------------------
        # Generate embeddings
        # -------------------------------------------------

        texts = [
            chunk.content
            for chunk in chunks
        ]

        embeddings = embedding_service.embed_texts(
            texts
        )

        # -------------------------------------------------
        # Store vectors in Qdrant
        # -------------------------------------------------

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

        # -------------------------------------------------
        # Mark document ready
        # -------------------------------------------------

        document.status = DocumentStatus.READY

        document_repository.update(
            db=db,
            document=document,
        )

        # -------------------------------------------------
        # Mark job completed
        # -------------------------------------------------

        job_service.mark_completed(
            db=db,
            job=job,
        )

        logger.info(
            "Document %s completed.",
            document_id,
        )

    # -----------------------------------------------------
    # Error handling
    # -----------------------------------------------------

    except Exception as exc:

        db.rollback()

        logger.exception(
            "Failed processing document %s",
            document_id,
        )

        try:

            job = job_repository.get(
                db=db,
                job_id=job_id,
            )

            document = document_repository.get(
                db=db,
                document_id=document_id,
            )

            # ---------------------------------------------
            # Mark job failed
            # ---------------------------------------------

            if job is not None:

                job_service.mark_failed(
                    db=db,
                    job=job,
                    error_message=str(exc),
                )

            # ---------------------------------------------
            # Mark document failed
            # ---------------------------------------------

            if document is not None:

                document.status = (
                    DocumentStatus.FAILED
                )

                document_repository.update(
                    db=db,
                    document=document,
                )

        except Exception:

            logger.exception(
                "Failed updating job/document failure state "
                "for document %s",
                document_id,
            )

    finally:

        db.close()


# ---------------------------------------------------------
# Worker Loop
# ---------------------------------------------------------

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

            payload = json.loads(
                raw_job
            )

            process_job(
                payload
            )

        except Exception:

            logger.exception(
                "Invalid job received from Redis."
            )


# ---------------------------------------------------------
# Entry Point
# ---------------------------------------------------------

if __name__ == "__main__":

    run_worker()