from uuid import UUID, uuid4

from qdrant_client.models import (
    Distance,
    PointStruct,
    VectorParams,
)

from app.core.config import settings
from app.db.qdrant import qdrant_client
from app.services.chunking.text_chunker import TextChunk


class VectorStore:

    def __init__(self):
        self.collection_name = settings.qdrant_collection

    def create_collection(self) -> None:

        collections = qdrant_client.get_collections()

        existing = {
            collection.name
            for collection in collections.collections
        }

        if self.collection_name in existing:
            return

        qdrant_client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=384,
                distance=Distance.COSINE,
            ),
        )

    def add_chunks(
        self,
        document_id: UUID,
        chunks: list[TextChunk],
        embeddings: list[list[float]],
    ) -> None:

        points = []

        for chunk, embedding in zip(
            chunks,
            embeddings,
        ):
            payload = {
                "document_id": str(document_id),
                "content": chunk.content,
                "metadata": chunk.metadata,
            }

            points.append(
                PointStruct(
                    id=str(uuid4()),
                    vector=embedding,
                    payload=payload,
                )
            )

        if points:
            qdrant_client.upsert(
                collection_name=self.collection_name,
                points=points,
            )

    def search(
        self,
        embedding: list[float],
        limit: int = 5,
    ):

        return qdrant_client.query_points(
            collection_name=self.collection_name,
            query=embedding,
            limit=limit,
            with_payload=True,
        ).points