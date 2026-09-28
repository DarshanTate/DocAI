import json
import time
from pathlib import Path

from app.services.retrieval.retrieval_service import (
    RetrievalService,
)


class RAGBenchmark:

    def __init__(self):
        self.retrieval_service = RetrievalService()

    def load_dataset(
        self,
        file_path: str,
    ):

        with open(
            file_path,
            "r",
            encoding="utf-8",
        ) as file:

            return json.load(file)

    def run(
        self,
        dataset_path: str,
    ):

        dataset = self.load_dataset(
            dataset_path
        )

        results = []

        for item in dataset:

            start = time.perf_counter()

            retrieved = (
                self.retrieval_service.retrieve(
                    question=item["question"],
                    top_k=5,
                )
            )

            latency = (
                time.perf_counter() - start
            )

            retrieved_ids = [
                str(
                    result.payload.get(
                        "document_id"
                    )
                )
                for result in retrieved
            ]

            results.append(
                {
                    "question": item["question"],
                    "retrieved_document_ids": retrieved_ids,
                    "relevant_document_ids": item[
                        "relevant_document_ids"
                    ],
                    "retrieval_latency_ms": round(
                        latency * 1000,
                        2,
                    ),
                }
            )

        return results