from uuid import UUID

from app.services.embeddings.embedding_service import EmbeddingService
from app.services.retrieval.vector_store import VectorStore


DOCUMENT_ID = "1dfec25f-86b4-4c6a-a3cf-8a6a4ec3cace"
OWNER_ID = "167316b8-f77b-4fc0-9576-b5af020bb21c"

QUESTIONS = [
    "What is the name of the person mentioned in the document?",
    "What ML model is used in the project Adaptive Traffic Signal Control?",
    "What is the tech stack for the project AppBuilder?",
]


embedding_service = EmbeddingService()
vector_store = VectorStore()


for question in QUESTIONS:

    print("\n" + "=" * 80)
    print("QUESTION:")
    print(question)
    print("=" * 80)

    embedding = embedding_service.embed_text(question)

    results = vector_store.search(
        embedding=embedding,
        owner_id=UUID(OWNER_ID),
        document_ids=[UUID(DOCUMENT_ID)],
        limit=5,
    )

    if not results:
        print("❌ No results retrieved.")
        continue

    for rank, result in enumerate(results, start=1):

        payload = result.payload or {}

        print(f"\n--- RESULT {rank} ---")

        print(
            "Qdrant score:",
            round(float(result.score), 4),
        )

        print(
            "Metadata:",
            payload.get("metadata", {}),
        )

        print("\nCONTENT:")
        print(payload.get("content", ""))

    print()