from uuid import UUID

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(min_length=1, max_length=5000)


class QueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)

    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
    )

    document_ids: list[UUID] = Field(
        default_factory=list,
        max_length=20,
    )

    chat_history: list[ChatMessage] = Field(
        default_factory=list,
        max_length=20,
    )


class SourceResponse(BaseModel):
    source_number: int
    document_id: str
    content: str
    score: float
    reranker_score: float = 0.0
    metadata: dict


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceResponse]