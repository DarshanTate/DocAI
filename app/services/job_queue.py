import json
from uuid import UUID

from app.db.redis import redis_client


QUEUE_NAME = "docai:document_processing"


class JobQueue:

    def enqueue_document_processing(
        self,
        job_id: UUID,
        document_id: UUID,
    ) -> None:

        job = {
            "job_id": str(job_id),
            "document_id": str(document_id),
        }

        redis_client.rpush(
            QUEUE_NAME,
            json.dumps(job),
        )