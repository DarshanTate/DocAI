from app.services.retrieval.vector_store import VectorStore


class ContextBuilder:

    def __init__(self):
        self.vector_store = VectorStore()

    def build(
        self,
        results,
    ) -> str:

        context_parts = []

        for index, result in enumerate(results, start=1):

            payload = result.payload

            content = payload.get(
                "content",
                "",
            )

            metadata = payload.get(
                "metadata",
                {},
            )

            context_parts.append(
                f"""
SOURCE {index}

Document ID:
{payload.get("document_id")}

Metadata:
{metadata}

Content:
{content}
""".strip()
            )

        return "\n\n".join(context_parts)