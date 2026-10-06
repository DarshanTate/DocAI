# tests/evaluation/run_context_relevance.py

import os
import json
import statistics
from pathlib import Path

os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://docai:docai_password@localhost:5432/docai"
)
os.environ["QDRANT_URL"] = "http://localhost:6333"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"

from app.services.embeddings.embedding_service import EmbeddingService
from app.services.retrieval.vector_store import VectorStore
from app.services.retrieval.reranker import Reranker


DATASET_PATH = Path("tests/evaluation/docai_eval_dataset.json")

OWNER_ID = "c9fedf8d-bf92-4d95-b966-5b111334b657"

DOCUMENT_ID = "d40b5c7c-83ba-4428-9815-596d1c9dcbb9"

TOP_K = 5


def load_dataset():
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        return json.load(f)["questions"]


def keyword_score(content: str, keywords: list[str]) -> float:
    """
    Measures how many expected concepts appear in one retrieved chunk.
    """
    content = content.lower()

    if not keywords:
        return 0.0

    matched = sum(
        1 for keyword in keywords
        if keyword.lower() in content
    )

    return matched / len(keywords)


def evaluate_ranked_results(results, keywords):
    """
    Rank-aware context relevance.

    Instead of combining all top-5 chunks, each rank is
    evaluated independently.
    """

    scores = []

    for result in results:
        content = result.payload.get("content", "")

        score = keyword_score(
            content,
            keywords
        )

        scores.append(score)

    return scores


def main():

    questions = load_dataset()

    embedding_service = EmbeddingService()
    vector_store = VectorStore()
    reranker = Reranker()

    vector_scores = {
        1: [],
        3: [],
        5: [],
    }

    reranked_scores = {
        1: [],
        3: [],
        5: [],
    }

    reranker_improvements = []

    print("\n=== Context Relevance Benchmark ===\n")

    for item in questions:

        question = item["question"]
        keywords = item["expected_keywords"]

        embedding = embedding_service.embed_text(question)

        vector_results = vector_store.search(
            embedding=embedding,
            owner_id=OWNER_ID,
            document_ids=[DOCUMENT_ID],
            limit=TOP_K,
        )

        reranked_results = reranker.rerank(
            question,
            vector_results,
            top_k=TOP_K,
        )

        vector_rank_scores = evaluate_ranked_results(
            vector_results,
            keywords,
        )

        reranked_rank_scores = evaluate_ranked_results(
            reranked_results,
            keywords,
        )

        print(f"{item['id']}: {question}")

        for k in [1, 3, 5]:

            vector_score = max(
                vector_rank_scores[:k],
                default=0.0,
            )

            reranked_score = max(
                reranked_rank_scores[:k],
                default=0.0,
            )

            vector_scores[k].append(vector_score)
            reranked_scores[k].append(reranked_score)

            print(
                f"  @{k} "
                f"Vector={vector_score:.3f} "
                f"Reranked={reranked_score:.3f}"
            )

        improvement = (
            max(reranked_rank_scores[:5], default=0.0)
            - max(vector_rank_scores[:5], default=0.0)
        )

        reranker_improvements.append(improvement)

        print()

    print("\n=== FINAL RESULTS ===\n")

    for k in [1, 3, 5]:

        vector_avg = statistics.mean(
            vector_scores[k]
        )

        reranked_avg = statistics.mean(
            reranked_scores[k]
        )

        improvement = reranked_avg - vector_avg

        print(
            f"Context Relevance@{k}: "
            f"Vector={vector_avg * 100:.2f}% | "
            f"Reranked={reranked_avg * 100:.2f}% | "
            f"Improvement={improvement * 100:+.2f} pp"
        )

    average_lift = statistics.mean(
        reranker_improvements
    )

    print(
        f"\nAverage Reranker Lift@5: "
        f"{average_lift * 100:+.2f} pp"
    )


if __name__ == "__main__":
    main()