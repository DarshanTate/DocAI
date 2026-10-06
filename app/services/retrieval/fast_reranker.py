# app/services/retrieval/fast_reranker.py

from sentence_transformers import SentenceTransformer
import numpy as np


class FastReranker:

    def __init__(
        self,
        model_name="sentence-transformers/all-MiniLM-L6-v2",
    ):
        self.model = SentenceTransformer(model_name)

    def rerank(
        self,
        question,
        results,
        top_k=5,
    ):
        if not results:
            return []

        documents = [
            result.payload.get("content", "")
            for result in results
        ]

        query_embedding = self.model.encode(
            question,
            normalize_embeddings=True,
        )

        document_embeddings = self.model.encode(
            documents,
            normalize_embeddings=True,
        )

        scores = np.dot(
            document_embeddings,
            query_embedding,
        )

        ranked = sorted(
            zip(results, scores),
            key=lambda x: float(x[1]),
            reverse=True,
        )

        reranked = []

        for result, score in ranked[:top_k]:

            result.payload["reranker_score"] = float(
                score
            )

            reranked.append(result)

        return reranked
    