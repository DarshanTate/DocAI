import os
import statistics
import time
from pathlib import Path
import json

os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://docai:docai_password@localhost:5432/docai"
)
os.environ["QDRANT_URL"] = "http://localhost:6333"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"

from app.services.embeddings.embedding_service import EmbeddingService
from app.services.retrieval.vector_store import VectorStore
from app.services.retrieval.reranker import Reranker
from app.services.generation.llm_service import LLMService


DATASET_PATH = Path("tests/evaluation/docai_eval_dataset.json")

OWNER_ID = "c9fedf8d-bf92-4d95-b966-5b111334b657"
DOCUMENT_ID = "d40b5c7c-83ba-4428-9815-596d1c9dcbb9"

TOP_K = 5


def percentile(values, p):
    if not values:
        return 0.0

    values = sorted(values)

    index = (len(values) - 1) * p
    lower = int(index)
    upper = min(lower + 1, len(values) - 1)

    weight = index - lower

    return (
        values[lower]
        + (values[upper] - values[lower]) * weight
    )


def load_questions():
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        return json.load(f)["questions"]


def consume_stream(stream):
    """
    Consume the complete LLM stream and measure generation time.
    """
    output = []

    for token in stream:
        output.append(token)

    return "".join(output)


def main():

    import json

    questions = load_questions()

    embedding_service = EmbeddingService()
    vector_store = VectorStore()
    reranker = Reranker()
    llm = LLMService()

    embedding_latencies = []
    retrieval_latencies = []
    reranker_latencies = []
    generation_latencies = []
    total_latencies = []

    successful_queries = 0
    failed_queries = 0

    total_tokens = 0

    print("\n")
    print("=" * 80)
    print("DocAI END-TO-END PERFORMANCE BENCHMARK")
    print("=" * 80)
    print(f"Questions : {len(questions)}")
    print(f"Top-K     : {TOP_K}")
    print("=" * 80)

    benchmark_start = time.perf_counter()

    for item in questions:

        question = item["question"]

        print(
            f"\n[{item['id']}] "
            f"{question}"
        )

        query_start = time.perf_counter()

        try:

            # --------------------------------------------------
            # 1. Embedding
            # --------------------------------------------------

            start = time.perf_counter()

            embedding = embedding_service.embed_text(
                question
            )

            embedding_time = (
                time.perf_counter() - start
            ) * 1000

            embedding_latencies.append(
                embedding_time
            )

            # --------------------------------------------------
            # 2. Vector retrieval
            # --------------------------------------------------

            start = time.perf_counter()

            vector_results = vector_store.search(
                embedding=embedding,
                owner_id=OWNER_ID,
                document_ids=[DOCUMENT_ID],
                limit=TOP_K * 3,
            )

            retrieval_time = (
                time.perf_counter() - start
            ) * 1000

            retrieval_latencies.append(
                retrieval_time
            )

            if not vector_results:
                raise RuntimeError(
                    "No retrieval results"
                )

            # --------------------------------------------------
            # 3. Reranking
            # --------------------------------------------------

            start = time.perf_counter()

            reranked_results = reranker.rerank(
                question,
                vector_results,
                top_k=TOP_K,
            )

            reranker_time = (
                time.perf_counter() - start
            ) * 1000

            reranker_latencies.append(
                reranker_time
            )

            # --------------------------------------------------
            # 4. Build context
            # --------------------------------------------------

            context_parts = []

            for i, result in enumerate(
                reranked_results,
                start=1,
            ):

                payload = result.payload or {}
                metadata = payload.get(
                    "metadata",
                    {},
                )

                page = metadata.get(
                    "page",
                    "unknown",
                )

                content = payload.get(
                    "content",
                    "",
                )

                context_parts.append(
                    f"[SOURCE {i} | PAGE {page}]\n"
                    f"{content}"
                )

            context = "\n\n".join(
                context_parts
            )

            # --------------------------------------------------
            # 5. LLM generation
            # --------------------------------------------------

            prompt = f"""
Answer the following question using ONLY
the provided document context.

Question:
{question}

Context:
{context}

Give a concise factual answer.
"""

            start = time.perf_counter()

            answer = consume_stream(
                llm.generate_stream(prompt)
            )

            generation_time = (
                time.perf_counter() - start
            ) * 1000

            generation_latencies.append(
                generation_time
            )

            # Approximate generated token count.
            generated_tokens = len(
                answer.split()
            )

            total_tokens += generated_tokens

            # --------------------------------------------------
            # 6. Total latency
            # --------------------------------------------------

            total_time = (
                time.perf_counter()
                - query_start
            ) * 1000

            total_latencies.append(
                total_time
            )

            successful_queries += 1

            print(
                f"  Embedding : {embedding_time:.2f} ms"
            )

            print(
                f"  Retrieval : {retrieval_time:.2f} ms"
            )

            print(
                f"  Reranker  : {reranker_time:.2f} ms"
            )

            print(
                f"  Generation: {generation_time:.2f} ms"
            )

            print(
                f"  Total     : {total_time:.2f} ms"
            )

        except Exception as exc:

            failed_queries += 1

            print(
                f"  FAILED: {exc}"
            )

    benchmark_time = (
        time.perf_counter()
        - benchmark_start
    )

    # ------------------------------------------------------
    # Statistics
    # ------------------------------------------------------

    def print_metric(name, values):

        if not values:
            print(
                f"{name}: No measurements"
            )
            return

        print(
            f"{name}: "
            f"mean={statistics.mean(values):.2f} ms | "
            f"p50={percentile(values, 0.50):.2f} ms | "
            f"p95={percentile(values, 0.95):.2f} ms | "
            f"p99={percentile(values, 0.99):.2f} ms"
        )

    print("\n")
    print("=" * 80)
    print("FINAL PERFORMANCE RESULTS")
    print("=" * 80)

    print_metric(
        "Embedding",
        embedding_latencies,
    )

    print_metric(
        "Vector Retrieval",
        retrieval_latencies,
    )

    print_metric(
        "Reranker",
        reranker_latencies,
    )

    print_metric(
        "LLM Generation",
        generation_latencies,
    )

    print_metric(
        "End-to-End",
        total_latencies,
    )

    print()

    print(
        f"Successful Queries : "
        f"{successful_queries}/{len(questions)}"
    )

    print(
        f"Failed Queries     : "
        f"{failed_queries}/{len(questions)}"
    )

    failure_rate = (
        failed_queries / len(questions)
        if questions
        else 0
    )

    print(
        f"Failure Rate       : "
        f"{failure_rate * 100:.2f}%"
    )

    if benchmark_time > 0:

        throughput = (
            successful_queries
            / benchmark_time
        )

        print(
            f"Throughput         : "
            f"{throughput:.2f} queries/sec"
        )

    print(
        f"Approx. Output Tokens : "
        f"{total_tokens}"
    )

    print("=" * 80)


if __name__ == "__main__":
    main()