from app.services.embeddings.embedding_service import EmbeddingService
from app.services.retrieval.vector_store import VectorStore


class RetrievalService:

    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()

    def retrieve(
        self,
        question: str,
        top_k: int = 5,
    ):

        embedding = self.embedding_service.embed_text(
            question
        )

        return self.vector_store.search(
            embedding=embedding,
            limit=top_k,
        )