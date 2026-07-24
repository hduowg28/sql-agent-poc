from enum import Enum
from typing import Any
from pydantic import Field
from app.schemas.base import AppBaseModel
from app.schemas.common import ResponseEnvelope


class ChatMessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(AppBaseModel):
    role: ChatMessageRole
    content: str = Field(..., min_length=1, max_length=4000)


class ChatRequest(AppBaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    session_id: str | None = None
    history: list[ChatMessage] = Field(default_factory=list)
    include_sql: bool = True
    include_raw_data: bool = False


class ChatExecutionMeta(AppBaseModel):
    execution_time_ms: float = Field(..., ge=0)
    tokens_used: int | None = Field(default=None, ge=0)
    model_name: str | None = "gemini-3.1-flash-lite"
    sql_executed: bool = False


class ChatResponseData(AppBaseModel):
    answer: str
    generated_sql: str | None = None
    data: list[dict[str, Any]] | None = None
    execution_meta: ChatExecutionMeta | None = None


class ChatResponse(AppBaseModel):
    success: bool = True
    answer: str
    generated_sql: str | None = None
    execution_meta: ChatExecutionMeta | None = None


class ChatEnvelopeResponse(ResponseEnvelope[ChatResponseData]):
    pass
