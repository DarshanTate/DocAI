from app.services.generation.context_builder import ContextBuilder
from app.services.generation.llm_service import LLMService
from app.services.generation.citation_service import CitationService
from app.services.retrieval.retrieval_service import RetrievalService


class RAGService:

    def __init__(self):
        self.retrieval_service = RetrievalService()
        self.context_builder = ContextBuilder()
        self.llm_service = LLMService()
        self.citation_service = CitationService()

    def answer(self, question: str, top_k: int = 5):

        results = self.retrieval_service.retrieve(
            question=question,
            top_k=top_k,
        )

        if not results:
            return (
                "I could not find relevant information in the uploaded documents.",
                [],
            )

        context = self.context_builder.build(results)

        prompt = f"""
You are DocAI, a document question-answering assistant.

Answer the user's question using ONLY the provided sources.

Rules:
1. Do not use outside knowledge.
2. Do not invent facts.
3. If the sources do not contain enough information, say so.
4. Cite the relevant source numbers in your answer using [Source N].

USER QUESTION:
{question}

SOURCES:
{context}

ANSWER:
"""

        answer = self.llm_service.generate(prompt)

        citations = self.citation_service.build_citations(results)

        return answer, citations