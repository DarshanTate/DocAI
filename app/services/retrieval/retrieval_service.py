from uuid import UUID

from app.services.retrieval.hybrid_retrieval import HybridRetrieval
from app.services.retrieval.reranker import Reranker


class RetrievalService:
    def __init__(self):
        self.hybrid_retrieval = HybridRetrieval()
        self.reranker = Reranker()

    def retrieve(
        self,
        question: str,
        owner_id: UUID,
        document_ids: list[UUID] | None = None,
        top_k: int = 5,
    ):
        # Retrieve a larger candidate set first.
        candidates = self.hybrid_retrieval.retrieve(
            question=question,
            owner_id=owner_id,
            document_ids=document_ids,
            top_k=top_k * 3,
        )

        if not candidates:
            return []

        # Rerank the larger candidate set.
        results = self.reranker.rerank(
            question=question,
            results=candidates,
            top_k=top_k,
        )

        return results