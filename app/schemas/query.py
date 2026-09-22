from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)


class SourceResponse(BaseModel):
    source_number: int
    document_id: str
    content: str
    score: float
    metadata: dict


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceResponse]