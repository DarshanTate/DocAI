# app/services/retrieval/reranker.py

from sentence_transformers import CrossEncoder


class Reranker:

    def __init__(
        self,
        model_name="cross-encoder/ms-marco-MiniLM-L-6-v2",
        batch_size=32,
    ):
        self.model = CrossEncoder(model_name)
        self.batch_size = batch_size

    def rerank(
        self,
        question,
        results,
        top_k=5,
    ):
        if not results:
            return []

        # Only rerank the candidates we actually need.
        candidates = results[:top_k * 2]

        pairs = [
            (
                question,
                result.payload.get("content", "")
            )
            for result in candidates
        ]

        scores = self.model.predict(
            pairs,
            batch_size=self.batch_size,
            show_progress_bar=False,
        )

        ranked = sorted(
            zip(candidates, scores),
            key=lambda item: float(item[1]),
            reverse=True,
        )

        reranked = []

        for result, score in ranked[:top_k]:
            result.payload["reranker_score"] = float(score)
            reranked.append(result)

        return reranked