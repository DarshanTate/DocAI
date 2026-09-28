class RetrievalMetrics:

    @staticmethod
    def recall_at_k(
        retrieved_ids: list[str],
        relevant_ids: list[str],
    ) -> float:

        if not relevant_ids:
            return 0.0

        retrieved = set(retrieved_ids)
        relevant = set(relevant_ids)

        hits = len(
            retrieved.intersection(relevant)
        )

        return hits / len(relevant)

    @staticmethod
    def precision_at_k(
        retrieved_ids: list[str],
        relevant_ids: list[str],
    ) -> float:

        if not retrieved_ids:
            return 0.0

        retrieved = set(retrieved_ids)
        relevant = set(relevant_ids)

        hits = len(
            retrieved.intersection(relevant)
        )

        return hits / len(retrieved_ids)

    @staticmethod
    def mrr(
        retrieved_ids: list[str],
        relevant_ids: list[str],
    ) -> float:

        relevant = set(relevant_ids)

        for rank, document_id in enumerate(
            retrieved_ids,
            start=1,
        ):
            if document_id in relevant:
                return 1.0 / rank

        return 0.0