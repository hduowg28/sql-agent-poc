from enum import Enum
from typing import Any
from pydantic import Field
from app.schemas.base import AppBaseModel
from app.schemas.common import ResponseEnvelope


class ChatMessageRole(str, Enum):
    """Supported roles in multi-turn conversation history."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(AppBaseModel):
    """Representation of a single message within conversation history."""

    role: ChatMessageRole = Field(
        ...,
        description="Role of the message sender.",
        examples=[ChatMessageRole.USER],
    )
    content: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="Text content of the message.",
        examples=["Show me total sales for 2025."],
    )


class ChatRequest(AppBaseModel):
    """
    Request payload schema for natural language database query endpoint.
    """

    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Natural language question to query the database.",
        examples=["How many total users are registered in the database?"],
    )
    session_id: str | None = Field(
        default=None,
        description="Optional session/conversation ID for multi-turn history tracking.",
        examples=["sess_987654"],
    )
    history: list[ChatMessage] = Field(
        default_factory=list,
        description="Prior conversation history context for agent multi-turn awareness.",
    )
    include_sql: bool = Field(
        default=True,
        description="Whether to include generated SQL query in the response.",
    )
    include_raw_data: bool = Field(
        default=False,
        description="Whether to include raw tabular execution results.",
    )


class ChatExecutionMeta(AppBaseModel):
    """Agent execution telemetry metrics."""

    execution_time_ms: float = Field(
        ...,
        ge=0,
        description="Total agent execution time in milliseconds.",
        examples=[452.18],
    )
    tokens_used: int | None = Field(
        default=None,
        ge=0,
        description="Total LLM tokens consumed for processing.",
        examples=[320],
    )
    model_name: str | None = Field(
        default="gemini-3.1-flash-lite",
        description="LLM model identifier used by the SQL agent.",
        examples=["gemini-3.1-flash-lite"],
    )
    sql_executed: bool = Field(
        default=False,
        description="Indicates if a SQL query was executed during processing.",
    )


class ChatResponseData(AppBaseModel):
    """Payload data returned by the SQL Chat Agent."""

    answer: str = Field(
        ...,
        description="Natural language answer synthesized by the SQL agent.",
        examples=["There are 1,250 total registered users."],
    )
    generated_sql: str | None = Field(
        default=None,
        description="The generated SQL statement executed against the database.",
        examples=["SELECT COUNT(*) FROM users;"],
    )
    data: list[dict[str, Any]] | None = Field(
        default=None,
        description="Raw tabular result set returned by database query execution.",
    )
    execution_meta: ChatExecutionMeta | None = Field(
        default=None,
        description="Execution performance telemetry and token usage details.",
    )


class ChatResponse(AppBaseModel):
    """
    Response schema for the SQL Agent chat endpoint.
    Maintains compatibility with simple response format while extending AppBaseModel.
    """

    success: bool = Field(
        default=True,
        description="Indicates whether the query operation succeeded.",
        examples=[True],
    )
    answer: str = Field(
        ...,
        description="Natural language answer synthesized by the SQL agent.",
        examples=["There are 1,250 total registered users."],
    )
    generated_sql: str | None = Field(
        default=None,
        description="The generated SQL statement executed against the database.",
        examples=["SELECT COUNT(*) FROM users;"],
    )
    execution_meta: ChatExecutionMeta | None = Field(
        default=None,
        description="Execution performance telemetry and usage details.",
    )


class ChatEnvelopeResponse(ResponseEnvelope[ChatResponseData]):
    """
    Generic envelope response schema for enterprise API gateways.
    """

    pass

