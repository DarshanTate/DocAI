import json

from app.db.redis import redis_client


QUEUE_NAME = "docai:document_processing"


class JobQueue:

    def enqueue_document_processing(
        self,
        document_id: str,
    ) -> None:

        job = {
            "document_id": document_id,
        }

        redis_client.rpush(
            QUEUE_NAME,
            json.dumps(job),
        )