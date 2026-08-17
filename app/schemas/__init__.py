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
from app.schemas.common import ErrorDetail, ErrorResponse, ResponseEnvelope
from app.schemas.health import HealthCheckResponse, HealthCheckResponseData
from app.schemas.sql import (
    ColumnSchemaInfo,
    DatabaseSchemaResponse,
    SQLExecutionRequest,
    SQLQueryResult,
    TableSchemaInfo,
)

from app.schemas.customer import CustomerCreate, CustomerResponse

__all__ = [
    # Base
    "AppBaseModel",
    "TimestampMixin",
    # Common / Generic
    "ResponseEnvelope",
    "ErrorDetail",
    "ErrorResponse",
    # Customer Domain
    "CustomerCreate",
    "CustomerResponse",
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
