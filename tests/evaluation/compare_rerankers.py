import os
import time
import statistics
import json
from pathlib import Path

os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://docai:docai_password@localhost:5432/docai"
)
os.environ["QDRANT_URL"] = "http://localhost:6333"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"

from app.services.embeddings.embedding_service import EmbeddingService
from app.services.retrieval.vector_store import VectorStore
from app.services.retrieval.reranker import Reranker
from app.services.retrieval.fast_reranker import FastReranker


DATASET_PATH = Path(
    "tests/evaluation/docai_eval_dataset.json"
)

OWNER_ID = "c9fedf8d-bf92-4d95-b966-5b111334b657"

DOCUMENT_ID = "d40b5c7c-83ba-4428-9815-596d1c9dcbb9"

TOP_K = 5


def recall_at_k(results, gold_pages, k):

    retrieved_pages = [
        result.payload
        .get("metadata", {})
        .get("page")
        for result in results[:k]
    ]

    return int(
        any(
            page in gold_pages
            for page in retrieved_pages
        )
    )


def benchmark():

    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        questions = json.load(f)["questions"]

    embedding_service = EmbeddingService()

    vector_store = VectorStore()

    cross_encoder = Reranker()

    fast_reranker = FastReranker()

    cross_times = []
    fast_times = []

    cross_hits = []
    fast_hits = []

    print("\n")
    print("=" * 80)
    print("DOCIA RERANKER COMPARISON")
    print("=" * 80)

    for item in questions:

        question = item["question"]

        gold_pages = item["gold_pdf_pages"]

        embedding = embedding_service.embed_text(
            question
        )

        candidates = vector_store.search(
            embedding=embedding,
            owner_id=OWNER_ID,
            document_ids=[DOCUMENT_ID],
            limit=TOP_K * 3,
        )

        # ---------------------------------------------
        # CrossEncoder
        # ---------------------------------------------

        start = time.perf_counter()

        cross_results = cross_encoder.rerank(
            question,
            candidates,
            top_k=TOP_K,
        )

        cross_time = (
            time.perf_counter() - start
        ) * 1000

        cross_times.append(cross_time)

        cross_hits.append(
            recall_at_k(
                cross_results,
                gold_pages,
                TOP_K,
            )
        )

        # ---------------------------------------------
        # Fast bi-encoder
        # ---------------------------------------------

        start = time.perf_counter()

        fast_results = fast_reranker.rerank(
            question,
            candidates,
            top_k=TOP_K,
        )

        fast_time = (
            time.perf_counter() - start
        ) * 1000

        fast_times.append(fast_time)

        fast_hits.append(
            recall_at_k(
                fast_results,
                gold_pages,
                TOP_K,
            )
        )

        print(
            f"{item['id']} | "
            f"CrossEncoder={cross_time:.2f} ms | "
            f"Fast={fast_time:.2f} ms"
        )

    cross_recall = statistics.mean(
        cross_hits
    )

    fast_recall = statistics.mean(
        fast_hits
    )

    cross_mean = statistics.mean(
        cross_times
    )

    fast_mean = statistics.mean(
        fast_times
    )

    speedup = (
        cross_mean / fast_mean
        if fast_mean > 0
        else 0
    )

    print("\n")
    print("=" * 80)
    print("FINAL COMPARISON")
    print("=" * 80)

    print(
        f"CrossEncoder latency : "
        f"{cross_mean:.2f} ms"
    )

    print(
        f"Fast reranker latency: "
        f"{fast_mean:.2f} ms"
    )

    print(
        f"Speedup               : "
        f"{speedup:.2f}x"
    )

    print()

    print(
        f"CrossEncoder Recall@5: "
        f"{cross_recall * 100:.2f}%"
    )

    print(
        f"Fast Recall@5        : "
        f"{fast_recall * 100:.2f}%"
    )

    print(
        f"Recall difference     : "
        f"{(fast_recall - cross_recall) * 100:+.2f} pp"
    )

    print("=" * 80)


if __name__ == "__main__":
    benchmark()