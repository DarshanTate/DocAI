import os
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
from app.services.generation.llm_service import LLMService


DATASET_PATH = Path("tests/evaluation/docai_eval_dataset.json")

OWNER_ID = "c9fedf8d-bf92-4d95-b966-5b111334b657"
DOCUMENT_ID = "d40b5c7c-83ba-4428-9815-596d1c9dcbb9"

TOP_K = 5


def load_dataset():
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        return json.load(f)["questions"]


def build_context(results):
    sources = []

    for index, result in enumerate(results, start=1):
        payload = result.payload or {}
        metadata = payload.get("metadata", {})

        sources.append(
            {
                "source_id": f"S{index}",
                "page": metadata.get("page"),
                "content": payload.get("content", ""),
            }
        )

    return sources


def generate_answer(llm, question, sources):
    context = "\n\n".join(
        f"[{s['source_id']} | Page {s['page']}]\n{s['content']}"
        for s in sources
    )

    prompt = f"""
Answer the question using ONLY the provided context.

For every factual claim, include the source ID that supports it.

Use citations exactly like:
[ S1 ]
[ S2 ]

Do not invent citations.

Question:
{question}

Context:
{context}

Answer:
"""

    answer = ""

    for token in llm.generate_stream(prompt):
        answer += token

    return answer.strip()


def evaluate_citations(llm, question, answer, sources):
    context = "\n\n".join(
        f"[{s['source_id']} | Page {s['page']}]\n{s['content']}"
        for s in sources
    )

    prompt = f"""
You are evaluating citations in a RAG system.

Question:
{question}

Retrieved sources:
{context}

Generated answer:
{answer}

For every factual claim in the answer, determine whether its cited
source actually supports that claim.

Score:

citation_accuracy:
Fraction of citations that correctly support the claim they are attached to.

citation_completeness:
Fraction of important factual claims that have a citation.

Return ONLY valid JSON:

{{
  "citation_accuracy": 0.0,
  "citation_completeness": 0.0,
  "reason": "short explanation"
}}
"""

    raw = ""

    for token in llm.generate_stream(prompt):
        raw += token

    raw = raw.strip()

    try:
        start = raw.find("{")
        end = raw.rfind("}") + 1

        if start == -1 or end == 0:
            raise ValueError("No JSON found")

        return json.loads(raw[start:end])

    except Exception as exc:
        print("Invalid evaluator response:")
        print(raw)

        return {
            "citation_accuracy": 0.0,
            "citation_completeness": 0.0,
            "reason": f"Parsing failed: {exc}",
        }


def main():

    questions = load_dataset()

    embedding_service = EmbeddingService()
    vector_store = VectorStore()
    reranker = Reranker()
    llm = LLMService()

    results = []

    print("\n")
    print("=" * 80)
    print("DocAI CITATION ACCURACY BENCHMARK")
    print("=" * 80)
    print(f"Questions : {len(questions)}")
    print(f"Top-K     : {TOP_K}")
    print("=" * 80)

    for item in questions:

        question = item["question"]

        print("\n" + "-" * 80)
        print(f"{item['id']}: {question}")
        print("-" * 80)

        embedding = embedding_service.embed_text(question)

        vector_results = vector_store.search(
            embedding=embedding,
            owner_id=OWNER_ID,
            document_ids=[DOCUMENT_ID],
            limit=TOP_K * 3,
        )

        if not vector_results:
            print("No results.")
            continue

        reranked_results = reranker.rerank(
            question,
            vector_results,
            top_k=TOP_K,
        )

        sources = build_context(reranked_results)

        answer = generate_answer(
            llm,
            question,
            sources,
        )

        print("\nGenerated Answer:")
        print(answer)

        evaluation = evaluate_citations(
            llm,
            question,
            answer,
            sources,
        )

        accuracy = float(
            evaluation.get("citation_accuracy", 0)
        )

        completeness = float(
            evaluation.get("citation_completeness", 0)
        )

        print("\nCitation Evaluation:")
        print(f"  Accuracy     : {accuracy:.2f}")
        print(f"  Completeness : {completeness:.2f}")
        print(f"  Reason       : {evaluation.get('reason', '')}")

        results.append(
            {
                "id": item["id"],
                "question": question,
                "answer": answer,
                "citation_accuracy": accuracy,
                "citation_completeness": completeness,
                "reason": evaluation.get("reason", ""),
            }
        )

    if not results:
        print("No results.")
        return

    avg_accuracy = sum(
        r["citation_accuracy"]
        for r in results
    ) / len(results)

    avg_completeness = sum(
        r["citation_completeness"]
        for r in results
    ) / len(results)

    print("\n")
    print("=" * 80)
    print("FINAL CITATION RESULTS")
    print("=" * 80)

    print(
        f"Citation Accuracy     : "
        f"{avg_accuracy * 100:.2f}%"
    )

    print(
        f"Citation Completeness : "
        f"{avg_completeness * 100:.2f}%"
    )

    print("=" * 80)

    output_path = Path(
        "tests/evaluation/citation_benchmark_results.json"
    )

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "questions": len(results),
                "metrics": {
                    "citation_accuracy": avg_accuracy,
                    "citation_completeness": avg_completeness,
                },
                "results": results,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    print(
        f"\nDetailed results saved to: {output_path}"
    )


if __name__ == "__main__":
    main()