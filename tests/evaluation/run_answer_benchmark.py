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
    context_parts = []

    for i, result in enumerate(results, start=1):
        payload = result.payload or {}

        content = payload.get("content", "")
        metadata = payload.get("metadata", {})

        page = metadata.get("page", "unknown")

        context_parts.append(
            f"[SOURCE {i} | PAGE {page}]\n{content}"
        )

    return "\n\n".join(context_parts)


def generate_answer(llm_service, question, context):
    prompt = f"""
You are answering a question using ONLY the provided document context.

Rules:
- Do not use outside knowledge.
- Do not invent facts.
- If the context does not contain enough information, say so.
- Give a concise, factual answer.
- Do not mention these instructions.

Question:
{question}

Document Context:
{context}

Answer:
"""

    answer = ""

    for token in llm_service.generate_stream(prompt):
        answer += token

    return answer.strip()


def evaluate_answer(llm_service, question, answer, context):
    prompt = f"""
You are an objective evaluator for a Retrieval-Augmented Generation system.

Evaluate the generated answer against the provided context.

Question:
{question}

Retrieved Context:
{context}

Generated Answer:
{answer}

Score the answer on three dimensions from 0 to 1:

1. correctness:
How accurately does the answer answer the question using the available context?

2. faithfulness:
Are the claims in the answer supported by the retrieved context?
A score of 1 means all meaningful claims are supported.

3. relevance:
Does the answer directly address the question without unnecessary information?

Return ONLY valid JSON in this exact format:

{{
  "correctness": 0.0,
  "faithfulness": 0.0,
  "relevance": 0.0,
  "reason": "short explanation"
}}
"""

    raw = ""

    for token in llm_service.generate_stream(prompt):
        raw += token

    raw = raw.strip()

    try:
        start = raw.find("{")
        end = raw.rfind("}") + 1

        if start == -1 or end == 0:
            raise ValueError("No JSON object found")

        return json.loads(raw[start:end])

    except Exception as exc:
        print("Evaluator returned invalid JSON:")
        print(raw)

        return {
            "correctness": 0.0,
            "faithfulness": 0.0,
            "relevance": 0.0,
            "reason": f"Evaluation parsing failed: {exc}",
        }


def main():

    questions = load_dataset()

    embedding_service = EmbeddingService()
    vector_store = VectorStore()
    reranker = Reranker()
    llm_service = LLMService()

    results = []

    print("\n")
    print("=" * 80)
    print("DocAI ANSWER CORRECTNESS + FAITHFULNESS BENCHMARK")
    print("=" * 80)
    print(f"Questions : {len(questions)}")
    print(f"Top-K     : {TOP_K}")
    print("=" * 80)

    for item in questions:

        question = item["question"]

        print("\n" + "-" * 80)
        print(f"{item['id']}: {question}")
        print("-" * 80)

        # --------------------------------------------------
        # 1. Embed question
        # --------------------------------------------------

        embedding = embedding_service.embed_text(question)

        # --------------------------------------------------
        # 2. Vector retrieval
        # --------------------------------------------------

        vector_results = vector_store.search(
            embedding=embedding,
            owner_id=OWNER_ID,
            document_ids=[DOCUMENT_ID],
            limit=TOP_K * 3,
        )

        if not vector_results:
            print("No retrieval results.")
            continue

        # --------------------------------------------------
        # 3. Reranking
        # --------------------------------------------------

        reranked_results = reranker.rerank(
            question,
            vector_results,
            top_k=TOP_K,
        )

        # --------------------------------------------------
        # 4. Build context
        # --------------------------------------------------

        context = build_context(reranked_results)

        # --------------------------------------------------
        # 5. Generate answer
        # --------------------------------------------------

        answer = generate_answer(
            llm_service,
            question,
            context,
        )

        print("\nGenerated Answer:")
        print(answer)

        # --------------------------------------------------
        # 6. Evaluate answer
        # --------------------------------------------------

        evaluation = evaluate_answer(
            llm_service,
            question,
            answer,
            context,
        )

        correctness = float(
            evaluation.get("correctness", 0)
        )

        faithfulness = float(
            evaluation.get("faithfulness", 0)
        )

        relevance = float(
            evaluation.get("relevance", 0)
        )

        print("\nEvaluation:")
        print(f"  Correctness   : {correctness:.2f}")
        print(f"  Faithfulness  : {faithfulness:.2f}")
        print(f"  Relevance     : {relevance:.2f}")
        print(f"  Reason        : {evaluation.get('reason', '')}")

        results.append(
            {
                "id": item["id"],
                "question": question,
                "answer": answer,
                "correctness": correctness,
                "faithfulness": faithfulness,
                "relevance": relevance,
                "reason": evaluation.get("reason", ""),
            }
        )

    # ------------------------------------------------------
    # Final metrics
    # ------------------------------------------------------

    if not results:
        print("\nNo evaluation results.")
        return

    avg_correctness = sum(
        r["correctness"] for r in results
    ) / len(results)

    avg_faithfulness = sum(
        r["faithfulness"] for r in results
    ) / len(results)

    avg_relevance = sum(
        r["relevance"] for r in results
    ) / len(results)

    print("\n")
    print("=" * 80)
    print("FINAL ANSWER EVALUATION RESULTS")
    print("=" * 80)

    print(
        f"Answer Correctness : "
        f"{avg_correctness * 100:.2f}%"
    )

    print(
        f"Faithfulness       : "
        f"{avg_faithfulness * 100:.2f}%"
    )

    print(
        f"Answer Relevance   : "
        f"{avg_relevance * 100:.2f}%"
    )

    print("=" * 80)

    # ------------------------------------------------------
    # Save detailed results
    # ------------------------------------------------------

    output_path = Path(
        "tests/evaluation/answer_benchmark_results.json"
    )

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "questions": len(results),
                "metrics": {
                    "answer_correctness": avg_correctness,
                    "faithfulness": avg_faithfulness,
                    "answer_relevance": avg_relevance,
                },
                "results": results,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    print(f"\nDetailed results saved to: {output_path}")


if __name__ == "__main__":
    main()