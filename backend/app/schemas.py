from uuid import uuid4

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    session_id: str = Field(default_factory=lambda: str(uuid4()))


class Citation(BaseModel):
    source_name: str
    snippet: str


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
    trace_id: str
