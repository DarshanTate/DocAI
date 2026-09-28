from sentence_transformers import CrossEncoder


class Reranker:
    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
    ):
        self.model = CrossEncoder(model_name)

    def rerank(
        self,
        question: str,
        results,
        top_k: int = 5,
    ):
        if not results:
            return []

        pairs = [
            (
                question,
                result.payload.get("content", ""),
            )
            for result in results
        ]

        scores = self.model.predict(pairs)

        ranked = sorted(
            zip(results, scores),
            key=lambda item: float(item[1]),
            reverse=True,
        )

        reranked = []

        for result, score in ranked[:top_k]:
            result.payload["reranker_score"] = float(score)
            reranked.append(result)

        return reranked