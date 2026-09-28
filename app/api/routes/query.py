from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.rate_limit import limiter
from app.db.database import get_db
from app.models.document import Document, DocumentStatus
from app.models.user import User
from app.schemas.query import (
    QueryRequest,
    QueryResponse,
    SourceResponse,
)
from app.services.generation.rag_service import RAGService
from app.services.structured.tabular_qa_service import TabularQAService
from fastapi.responses import StreamingResponse


router = APIRouter(
    prefix="/query",
    tags=["Query"],
)

rag_service = RAGService()
tabular_service = TabularQAService()


@router.post(
    "",
    response_model=QueryResponse,
)
@limiter.limit("30/minute")
def query_documents(
    request: Request,
    query_request: QueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # ---------------------------------------------------------
    # 1. Make sure the user has selected documents
    # ---------------------------------------------------------

    if not query_request.document_ids:
        return QueryResponse(
            answer="Please upload and process a document before asking a question.",
            sources=[],
        )

    # ---------------------------------------------------------
    # 2. Get ONLY documents owned by the current user
    #    and already processed
    # ---------------------------------------------------------

    requested_documents = list(
        db.scalars(
            select(Document).where(
                Document.id.in_(query_request.document_ids),
                Document.owner_id == current_user.id,
                Document.status == DocumentStatus.READY,
            )
        ).all()
    )

    # ---------------------------------------------------------
    # 3. Security check
    # ---------------------------------------------------------

    if not requested_documents:
        return QueryResponse(
            answer="No processed documents are available for this chat.",
            sources=[],
        )

    # ---------------------------------------------------------
    # 4. Make sure every requested document belongs to the user
    # ---------------------------------------------------------

    if len(requested_documents) != len(
        set(query_request.document_ids)
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="One or more selected documents are not available.",
        )

    # ---------------------------------------------------------
    # 5. Structured documents
    # ---------------------------------------------------------

    structured_documents = [
        document
        for document in requested_documents
        if document.file_type in {
            "text/csv",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        }
    ]

    if structured_documents:

        # For now, use the first structured document.
        # Multi-spreadsheet reasoning can be added later.

        document = structured_documents[0]

        answer = tabular_service.answer(
            file_path=document.storage_path,
            question=query_request.question,
        )

        return QueryResponse(
            answer=answer,
            sources=[
                SourceResponse(
                    source_number=1,
                    document_id=str(document.id),
                    content="Structured spreadsheet analysis",
                    score=1.0,
                    metadata={
                        "filename": document.original_filename,
                        "type": "structured",
                    },
                )
            ],
        )

    # ---------------------------------------------------------
    # 6. Normal RAG
    # ---------------------------------------------------------

    answer, citations = rag_service.answer(
        question=query_request.question,
        owner_id=current_user.id,
        document_ids=[
            document.id for document in requested_documents
        ],
        top_k=query_request.top_k,
        chat_history=[
            message.model_dump()
            for message in query_request.chat_history
        ],
    )

    # ---------------------------------------------------------
    # 7. Convert citations into API response
    # ---------------------------------------------------------

    sources = [
        SourceResponse(
            source_number=citation["source_number"],
            document_id=citation["document_id"],
            content=citation["content"],
            score=citation["score"],
            reranker_score=citation["reranker_score"],
            metadata=citation["metadata"],
        )
        for citation in citations
    ]

    return QueryResponse(
        answer=answer,
        sources=sources,
    )

@router.post("/debug")
@limiter.limit("30/minute")
def debug_query(
    request: Request,
    query_request: QueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not query_request.document_ids:
        return {
            "question": query_request.question,
            "results": [],
        }

    requested_documents = list(
        db.scalars(
            select(Document).where(
                Document.id.in_(query_request.document_ids),
                Document.owner_id == current_user.id,
                Document.status == DocumentStatus.READY,
            )
        ).all()
    )

    if not requested_documents:
        raise HTTPException(
            status_code=404,
            detail="No processed documents found.",
        )

    retrieval_service = rag_service.retrieval_service

    results = retrieval_service.retrieve(
        question=query_request.question,
        owner_id=current_user.id,
        document_ids=[
            document.id
            for document in requested_documents
        ],
        top_k=query_request.top_k,
    )

    debug_results = []

    for index, result in enumerate(results, start=1):
        payload = result.payload or {}
        metadata = payload.get("metadata", {})

        debug_results.append({
            "rank": index,
            "document_id": payload.get("document_id"),
            "qdrant_score": float(result.score),
            "reranker_score": float(
                payload.get("reranker_score", 0.0)
            ),
            "content": payload.get("content", ""),
            "metadata": metadata,
        })

    return {
        "question": query_request.question,
        "result_count": len(debug_results),
        "results": debug_results,
    }

@router.post("/stream")
@limiter.limit("30/minute")
def stream_query(
    request: Request,
    query_request: QueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not query_request.document_ids:
        raise HTTPException(
            status_code=400,
            detail="Please upload and process a document first.",
        )

    requested_documents = list(
        db.scalars(
            select(Document).where(
                Document.id.in_(query_request.document_ids),
                Document.owner_id == current_user.id,
                Document.status == DocumentStatus.READY,
            )
        ).all()
    )

    if not requested_documents:
        raise HTTPException(
            status_code=404,
            detail="No processed documents are available.",
        )

    def generate():
        for chunk in rag_service.answer_stream(
            question=query_request.question,
            owner_id=current_user.id,
            document_ids=[
                document.id
                for document in requested_documents
            ],
            top_k=query_request.top_k,
            chat_history=[
                message.model_dump()
                for message in query_request.chat_history
            ],
        ):
            yield chunk

    return StreamingResponse(
        generate(),
        media_type="text/plain",
    )