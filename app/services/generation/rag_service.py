from uuid import UUID

from app.services.generation.citation_service import CitationService
from app.services.generation.context_builder import ContextBuilder
from app.services.generation.llm_service import LLMService
from app.services.retrieval.retrieval_service import RetrievalService


class RAGService:
    def __init__(self):
        self.retrieval_service = RetrievalService()
        self.context_builder = ContextBuilder()
        self.citation_service = CitationService()
        self.llm_service = LLMService()

    def answer_stream(
        self,
        question: str,
        owner_id: UUID,
        document_ids: list[UUID] | None = None,
        top_k: int = 5,
        chat_history: list | None = None,
    ):
        results = self.retrieval_service.retrieve(
            question=question,
            owner_id=owner_id,
            document_ids=document_ids,
            top_k=top_k,
        )

        if not results:
            yield "I could not find relevant information in the uploaded documents."
            return

        context = self.context_builder.build(results)

        conversation = self._build_conversation(
            chat_history or []
        )

        prompt = f"""
    You are a document question-answering assistant.

    Answer the user's question using ONLY the information
    provided in the document sources.

    Previous conversation:
    {conversation}

    Current question:
    {question}

    Document sources:
    {context}

    Rules:
    - Use the document sources as the primary source of truth.
    - Do not invent facts.
    - If the documents do not contain enough information, say so.
    - Use previous conversation to understand references such as
      "it", "they", "that", and "previous year".
    - Cite factual statements using [Source N].
    - Keep the answer concise.
    - Use bullets when appropriate.

    Answer:
    """

        for chunk in self.llm_service.generate_stream(prompt):
            yield chunk


        citations = self.citation_service.build_citations(results)

        return citations

    def _build_conversation(self, chat_history: list) -> str:
        if not chat_history:
            return "No previous conversation."

        messages = []

        for message in chat_history[-10:]:
            role = message.get("role")
            content = message.get("content")

            if role and content:
                messages.append(
                    f"{role.upper()}: {content}"
                )

        return "\n".join(messages)