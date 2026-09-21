import json
import time

from app.db.redis import redis_client
from app.services.document_repository import DocumentRepository
from app.services.ingestion_service import IngestionService
from app.services.job_queue import QUEUE_NAME
from app.processors.factory import DocumentProcessorFactory


document_repository = DocumentRepository()

processor_factory = DocumentProcessorFactory()

ingestion_service = IngestionService(
    processor_factory=processor_factory,
)


def run_worker():
    print("DocAI ingestion worker started.")

    while True:

        result = redis_client.blpop(
            QUEUE_NAME,
            timeout=5,
        )

        if result is None:
            continue

        _, raw_job = result

        job = json.loads(raw_job)

        document_id = job["document_id"]

        document = document_repository.get(
            document_id
        )

        if document is None:
            print(
                f"Document not found: {document_id}"
            )
            continue

        print(
            f"Processing: {document.original_filename}"
        )

        parsed_document = ingestion_service.process(
            document.storage_path
        )

        print(
            f"Extracted {len(parsed_document.elements)} "
            f"elements"
        )


if __name__ == "__main__":
    run_worker()