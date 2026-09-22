class CitationService:

    def build_citations(self, results):
        citations = []

        for index, result in enumerate(results, start=1):
            payload = result.payload or {}
            metadata = payload.get("metadata", {})

            citations.append(
                {
                    "source_number": index,
                    "document_id": payload.get("document_id"),
                    "score": result.score,
                    "content": payload.get("content", ""),
                    "metadata": metadata,
                }
            )

        return citations