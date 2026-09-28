class CitationService:

    def build_citations(self, results):
        citations = []

        for index, result in enumerate(results, start=1):
            payload = result.payload or {}
            metadata = payload.get("metadata", {})

            citations.append({
                "source_number": index,
                "document_id": payload.get("document_id"),
                "content": payload.get("content", ""),
                "score": float(result.score),
                "reranker_score": payload.get(
                    "reranker_score",
                    0.0,
                ),
                "metadata": metadata,
            })

        return citations