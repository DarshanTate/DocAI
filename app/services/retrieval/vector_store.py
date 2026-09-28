from uuid import UUID, uuid4

from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchAny,
    MatchValue,
    PointStruct,
    VectorParams,
)

from app.core.config import settings
from app.db.qdrant import qdrant_client
from app.services.chunking.text_chunker import TextChunk


class VectorStore:

    VECTOR_SIZE = 384

    def __init__(self):
        self.collection_name = settings.qdrant_collection

    def create_collection(self):
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
                size=self.VECTOR_SIZE,
                distance=Distance.COSINE,
            ),
        )

    def add_chunks(
        self,
        document_id: UUID,
        owner_id: UUID,
        chunks: list[TextChunk],
        embeddings: list[list[float]],
    ):
        points = []

        for chunk, embedding in zip(chunks, embeddings):

            payload = {
                "document_id": str(document_id),
                "owner_id": str(owner_id),
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
        owner_id: UUID,
        document_ids: list[UUID] | None = None,
        limit: int = 5,
    ):
        conditions = [
            FieldCondition(
                key="owner_id",
                match=MatchValue(
                    value=str(owner_id)
                ),
            )
        ]
    
        if document_ids:
            conditions.append(
                FieldCondition(
                    key="document_id",
                    match=MatchAny(
                        any=[
                            str(document_id)
                            for document_id in document_ids
                        ]
                    ),
                )
            )
    
        query_filter = Filter(
            must=conditions
        )
    
        return qdrant_client.query_points(
            collection_name=self.collection_name,
            query=embedding,
            query_filter=query_filter,
            limit=limit,
            with_payload=True,
        ).points