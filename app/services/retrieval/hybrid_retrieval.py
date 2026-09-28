from uuid import UUID

from app.services.embeddings.embedding_service import EmbeddingService
from app.services.retrieval.keyword_store import KeywordStore
from app.services.retrieval.vector_store import VectorStore


class HybridRetrieval:

    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()
        self.keyword_store = KeywordStore()

    def retrieve(
        self,
        question: str,
        owner_id: UUID,
        document_ids: list[UUID] | None = None,
        top_k: int = 5,
    ):
        query_embedding = self.embedding_service.embed_text(
            question
        )

        vector_results = self.vector_store.search(
            embedding=query_embedding,
            owner_id=owner_id,
            document_ids=document_ids,
            limit=top_k * 2,
        )

        if not vector_results:
            return []

        keyword_results = self.keyword_store.search(
            question=question,
            chunks=vector_results,
            limit=top_k * 2,
        )

        return self._combine_results(
            vector_results,
            keyword_results,
            top_k,
        )

    def _combine_results(
        self,
        vector_results,
        keyword_results,
        top_k,
    ):
        scores = {}

        for rank, result in enumerate(vector_results):
            key = self._result_key(result)

            scores.setdefault(
                key,
                {
                    "result": result,
                    "score": 0.0,
                },
            )

            scores[key]["score"] += (
                0.7 / (rank + 1)
            )

        for rank, item in enumerate(keyword_results):
            result, _bm25_score = item

            key = self._result_key(result)

            scores.setdefault(
                key,
                {
                    "result": result,
                    "score": 0.0,
                },
            )

            scores[key]["score"] += (
                0.3 / (rank + 1)
            )

        ranked = sorted(
            scores.values(),
            key=lambda item: item["score"],
            reverse=True,
        )

        return [
            item["result"]
            for item in ranked[:top_k]
        ]

    @staticmethod
    def _result_key(result):
        payload = result.payload or {}

        return (
            payload.get("document_id"),
            payload.get("content"),
        )