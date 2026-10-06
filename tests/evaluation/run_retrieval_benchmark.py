import json
import math
import os
import statistics
import time
from pathlib import Path
from uuid import UUID

os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://docai:docai_password@localhost:5432/docai"
)
os.environ["QDRANT_URL"] = "http://localhost:6333"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"

from app.services.embeddings.embedding_service import EmbeddingService
from app.services.retrieval.vector_store import VectorStore
from app.services.retrieval.reranker import Reranker


DATASET_PATH = Path(__file__).parent / "docai_eval_dataset.json"

OWNER_ID = UUID("c9fedf8d-bf92-4d95-b966-5b111334b657")
DOCUMENT_ID = UUID("d40b5c7c-83ba-4428-9815-596d1c9dcbb9")

K_VALUES = [1, 3, 5]


def load_dataset():
    with DATASET_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)["questions"]


def get_page(result):
    metadata = result.payload.get("metadata", {})
    return metadata.get("page")


def is_relevant(result, gold_pages):
    return get_page(result) in gold_pages


def reciprocal_rank(results, gold_pages):
    for rank, result in enumerate(results, start=1):
        if is_relevant(result, gold_pages):
            return 1.0 / rank
    return 0.0


def ndcg_at_k(results, gold_pages, k):
    results = results[:k]

    relevances = [
        1 if is_relevant(result, gold_pages) else 0
        for result in results
    ]

    dcg = 0.0

    for rank, relevance in enumerate(relevances, start=1):
        dcg += relevance / math.log2(rank + 1)

    total_relevant = sum(relevances)

    ideal_relevances = [1] * min(total_relevant, k)

    idcg = 0.0

    for rank, relevance in enumerate(ideal_relevances, start=1):
        idcg += relevance / math.log2(rank + 1)

    if idcg == 0:
        return 0.0

    return dcg / idcg


def recall_at_k(results, gold_pages, k):
    return int(any(
        is_relevant(result, gold_pages)
        for result in results[:k]
    ))


def precision_at_k(results, gold_pages, k):
    retrieved = results[:k]

    if not retrieved:
        return 0.0

    relevant = sum(
        is_relevant(result, gold_pages)
        for result in retrieved
    )

    return relevant / k


def percentile(values, percentile):
    if not values:
        return 0.0

    values = sorted(values)

    index = (len(values) - 1) * percentile / 100

    lower = math.floor(index)
    upper = math.ceil(index)

    if lower == upper:
        return values[lower]

    return (
        values[lower]
        + (values[upper] - values[lower])
        * (index - lower)
    )


def main():
    questions = load_dataset()

    embedding_service = EmbeddingService()
    vector_store = VectorStore()
    reranker = Reranker()

    vector_store.create_collection()

    vector_latencies = []
    rerank_latencies = []
    total_latencies = []

    vector_recalls = {k: [] for k in K_VALUES}
    reranked_recalls = {k: [] for k in K_VALUES}

    vector_precisions = {k: [] for k in K_VALUES}
    reranked_precisions = {k: [] for k in K_VALUES}

    vector_mrr = []
    reranked_mrr = []

    vector_ndcg = []
    reranked_ndcg = []

    print()
    print("=" * 80)
    print("DocAI RAG RETRIEVAL BENCHMARK")
    print("=" * 80)
    print(f"Questions : {len(questions)}")
    print(f"Document  : {DOCUMENT_ID}")
    print(f"K values  : {K_VALUES}")
    print("=" * 80)

    for item in questions:
        question = item["question"]
        gold_pages = set(item["gold_pdf_pages"])

        # ---------------------------------------------------------
        # Vector retrieval
        # ---------------------------------------------------------

        start = time.perf_counter()

        query_embedding = embedding_service.embed_text(question)

        vector_results = vector_store.search(
            embedding=query_embedding,
            owner_id=OWNER_ID,
            document_ids=[DOCUMENT_ID],
            limit=K_VALUES[-1],
        )

        vector_latency = (time.perf_counter() - start) * 1000

        # ---------------------------------------------------------
        # Reranking
        # ---------------------------------------------------------

        start = time.perf_counter()

        reranked_results = reranker.rerank(
            question=question,
            results=vector_results,
            top_k=K_VALUES[-1],
        )

        rerank_latency = (time.perf_counter() - start) * 1000

        total_latency = vector_latency + rerank_latency

        vector_latencies.append(vector_latency)
        rerank_latencies.append(rerank_latency)
        total_latencies.append(total_latency)

        # ---------------------------------------------------------
        # Retrieval metrics
        # ---------------------------------------------------------

        for k in K_VALUES:
            vector_recalls[k].append(
                recall_at_k(vector_results, gold_pages, k)
            )

            reranked_recalls[k].append(
                recall_at_k(reranked_results, gold_pages, k)
            )

            vector_precisions[k].append(
                precision_at_k(vector_results, gold_pages, k)
            )

            reranked_precisions[k].append(
                precision_at_k(reranked_results, gold_pages, k)
            )

        vector_mrr.append(
            reciprocal_rank(vector_results, gold_pages)
        )

        reranked_mrr.append(
            reciprocal_rank(reranked_results, gold_pages)
        )

        vector_ndcg.append(
            ndcg_at_k(vector_results, gold_pages, 5)
        )

        reranked_ndcg.append(
            ndcg_at_k(reranked_results, gold_pages, 5)
        )

        print(
            f"{item['id']} | "
            f"Vector MRR={vector_mrr[-1]:.3f} | "
            f"Reranked MRR={reranked_mrr[-1]:.3f} | "
            f"Latency={total_latency:.1f}ms"
        )

    # =============================================================
    # FINAL RESULTS
    # =============================================================

    print()
    print("=" * 80)
    print("FINAL RESULTS")
    print("=" * 80)

    print("\nRecall")

    for k in K_VALUES:
        vector_score = statistics.mean(vector_recalls[k])
        reranked_score = statistics.mean(reranked_recalls[k])

        print(
            f"Recall@{k}: "
            f"Vector={vector_score:.3f} | "
            f"Reranked={reranked_score:.3f}"
        )

    print("\nPrecision")

    for k in K_VALUES:
        vector_score = statistics.mean(vector_precisions[k])
        reranked_score = statistics.mean(reranked_precisions[k])

        print(
            f"Precision@{k}: "
            f"Vector={vector_score:.3f} | "
            f"Reranked={reranked_score:.3f}"
        )

    print("\nRanking Metrics")

    vector_mrr_score = statistics.mean(vector_mrr)
    reranked_mrr_score = statistics.mean(reranked_mrr)

    vector_ndcg_score = statistics.mean(vector_ndcg)
    reranked_ndcg_score = statistics.mean(reranked_ndcg)

    print(
        f"MRR:       "
        f"Vector={vector_mrr_score:.3f} | "
        f"Reranked={reranked_mrr_score:.3f}"
    )

    print(
        f"NDCG@5:    "
        f"Vector={vector_ndcg_score:.3f} | "
        f"Reranked={reranked_ndcg_score:.3f}"
    )

    print("\nReranker Lift")

    print(
        f"MRR lift: "
        f"{reranked_mrr_score - vector_mrr_score:+.3f}"
    )

    print(
        f"NDCG@5 lift: "
        f"{reranked_ndcg_score - vector_ndcg_score:+.3f}"
    )

    print("\nLatency")

    print(
        f"Vector search: "
        f"mean={statistics.mean(vector_latencies):.2f}ms | "
        f"p50={percentile(vector_latencies, 50):.2f}ms | "
        f"p95={percentile(vector_latencies, 95):.2f}ms"
    )

    print(
        f"Reranker: "
        f"mean={statistics.mean(rerank_latencies):.2f}ms | "
        f"p50={percentile(rerank_latencies, 50):.2f}ms | "
        f"p95={percentile(rerank_latencies, 95):.2f}ms"
    )

    print(
        f"Total: "
        f"mean={statistics.mean(total_latencies):.2f}ms | "
        f"p50={percentile(total_latencies, 50):.2f}ms | "
        f"p95={percentile(total_latencies, 95):.2f}ms"
    )

    print()
    print("=" * 80)
    print("Benchmark complete.")
    print("=" * 80)


if __name__ == "__main__":
    main()