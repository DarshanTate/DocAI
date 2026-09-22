from rank_bm25 import BM25Okapi


class KeywordStore:

    def search(self, question: str, chunks: list, limit: int = 5):
        if not chunks:
            return []

        documents = [
            chunk.payload.get("content", "")
            for chunk in chunks
        ]

        tokenized_documents = [
            document.lower().split()
            for document in documents
        ]

        bm25 = BM25Okapi(tokenized_documents)

        query_tokens = question.lower().split()

        scores = bm25.get_scores(query_tokens)

        ranked = sorted(
            zip(chunks, scores),
            key=lambda item: item[1],
            reverse=True,
        )

        return ranked[:limit]