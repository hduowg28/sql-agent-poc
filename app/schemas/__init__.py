from app.schemas.base import AppBaseModel, TimestampMixin
from app.schemas.chat import (
    ChatExecutionMeta,
    ChatMessage,
    ChatMessageRole,
    ChatRequest,
    ChatResponse,
    ChatResponseData,
    ChatEnvelopeResponse,
)
from app.schemas.common import (
    ErrorDetail,
    ErrorResponse,
    PaginatedMeta,
    PaginatedResponseEnvelope,
    PaginationParams,
    ResponseEnvelope,
)
from app.schemas.health import HealthCheckResponse, HealthCheckResponseData
from app.schemas.sql import (
    ColumnSchemaInfo,
    DatabaseSchemaResponse,
    SQLExecutionRequest,
    SQLQueryResult,
    TableSchemaInfo,
)

__all__ = [
    # Base
    "AppBaseModel",
    "TimestampMixin",
    # Common / Generic
    "ResponseEnvelope",
    "ErrorDetail",
    "ErrorResponse",
    "PaginationParams",
    "PaginatedMeta",
    "PaginatedResponseEnvelope",
    # Chat Domain
    "ChatMessageRole",
    "ChatMessage",
    "ChatRequest",
    "ChatExecutionMeta",
    "ChatResponseData",
    "ChatResponse",
    "ChatEnvelopeResponse",
    # SQL Domain
    "SQLExecutionRequest",
    "SQLQueryResult",
    "ColumnSchemaInfo",
    "TableSchemaInfo",
    "DatabaseSchemaResponse",
    # Health Domain
    "HealthCheckResponseData",
    "HealthCheckResponse",
]
