from typing import Any, Generic, TypeVar
from pydantic import Field
from app.schemas.base import AppBaseModel

DataT = TypeVar("DataT")


class ResponseEnvelope(AppBaseModel, Generic[DataT]):
    """
    Unified API Response Envelope for all endpoints.

    Provides a consistent response structure across services:
    - success: Indicates overall status.
    - message: Human-readable context or notice.
    - data: Typed payload matching the specific endpoint.
    - meta: Optional dictionary for request-level metadata (e.g. latency, request_id).
    """

    success: bool = Field(
        default=True,
        description="Indicates whether the API operation succeeded.",
        examples=[True],
    )
    message: str = Field(
        default="Operation completed successfully",
        description="Human-readable summary message.",
        examples=["Operation completed successfully"],
    )
    data: DataT | None = Field(
        default=None,
        description="The primary typed payload of the response.",
    )
    meta: dict[str, Any] | None = Field(
        default=None,
        description="Optional execution metadata or response context.",
    )


class ErrorDetail(AppBaseModel):
    """Specific field or contextual error item inside an ErrorResponse."""

    code: str = Field(
        ...,
        description="Machine-readable error classification code.",
        examples=["VALIDATION_ERROR", "NOT_FOUND"],
    )
    message: str = Field(
        ...,
        description="Detailed, human-readable message describing the specific error.",
        examples=["Question cannot be empty."],
    )
    field: str | None = Field(
        default=None,
        description="Target payload field associated with the error (if applicable).",
        examples=["question"],
    )


class ErrorResponse(AppBaseModel):
    """Standardized error envelope returned on HTTP 4xx / 5xx failures."""

    success: bool = Field(
        default=False,
        description="Always false for error responses.",
        examples=[False],
    )
    error: str = Field(
        ...,
        description="High-level error description or title.",
        examples=["Bad Request"],
    )
    details: list[ErrorDetail] = Field(
        default_factory=list,
        description="List of specific error details or validation failures.",
    )


class PaginationParams(AppBaseModel):
    """Reusable query parameter schema for paginated list endpoints."""

    page: int = Field(
        default=1,
        ge=1,
        description="1-indexed page number.",
        examples=[1],
    )
    page_size: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Number of records per page (max 100).",
        examples=[20],
    )


class PaginatedMeta(AppBaseModel):
    """Metadata accompanying paginated API payloads."""

    total_items: int = Field(..., ge=0, description="Total number of items available across all pages.")
    total_pages: int = Field(..., ge=0, description="Total computed pages.")
    page: int = Field(..., ge=1, description="Current page number.")
    page_size: int = Field(..., ge=1, description="Items per page.")


class PaginatedResponseEnvelope(ResponseEnvelope[list[DataT]], Generic[DataT]):
    """Generic envelope tailored specifically for paginated list endpoints."""

    pagination: PaginatedMeta | None = Field(
        default=None,
        description="Pagination metrics for list results.",
    )
