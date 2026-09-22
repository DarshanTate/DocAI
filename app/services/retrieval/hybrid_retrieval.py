from app.services.embeddings.embedding_service import EmbeddingService
from app.services.retrieval.vector_store import VectorStore


class HybridRetrieval:

    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()

    def retrieve(
        self,
        question: str,
        top_k: int = 5,
    ):
        query_embedding = self.embedding_service.embed_text(question)

        vector_results = self.vector_store.search(
            embedding=query_embedding,
            limit=top_k * 2,
        )

        if not vector_results:
            return []

        return self._combine_results(vector_results, top_k)

    def _combine_results(self, vector_results, top_k):

        scored_results = []

        for rank, result in enumerate(vector_results):
            vector_score = 1 / (rank + 1)

            scored_results.append(
                (
                    result,
                    vector_score,
                )
            )

        scored_results.sort(
            key=lambda item: item[1],
            reverse=True,
        )

        return [
            result
            for result, _ in scored_results[:top_k]
        ]