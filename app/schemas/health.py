from datetime import datetime, timezone
from pydantic import Field
from app.schemas.base import AppBaseModel
from app.schemas.common import ResponseEnvelope


class HealthCheckResponseData(AppBaseModel):
    """Diagnostic data payload for system health check endpoints."""

    status: str = Field(
        default="ok",
        description="Overall service operational status.",
        examples=["ok"],
    )
    version: str = Field(
        default="1.0.0",
        description="Application deployment version.",
        examples=["1.0.0"],
    )
    database_connected: bool = Field(
        ...,
        description="Database connection connectivity status.",
        examples=[True],
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Current UTC server timestamp.",
    )


class HealthCheckResponse(ResponseEnvelope[HealthCheckResponseData]):
    """Response envelope for system health check endpoint."""

    pass
