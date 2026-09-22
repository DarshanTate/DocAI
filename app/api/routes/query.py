from fastapi import APIRouter

from app.schemas.query import (
    QueryRequest,
    QueryResponse,
    SourceResponse,
)

from app.services.generation.rag_service import RAGService


router = APIRouter(
    prefix="/query",
    tags=["Query"],
)

rag_service = RAGService()


@router.post("", response_model=QueryResponse)
def query_documents(request: QueryRequest):

    answer, citations = rag_service.answer(
        question=request.question,
        top_k=request.top_k,
    )

    sources = [
        SourceResponse(
            source_number=citation["source_number"],
            document_id=citation["document_id"],
            content=citation["content"],
            score=citation["score"],
            metadata=citation["metadata"],
        )
        for citation in citations
    ]

    return QueryResponse(
        answer=answer,
        sources=sources,
    )