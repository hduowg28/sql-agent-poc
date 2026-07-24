from datetime import datetime, timezone
from pydantic import Field
from app.schemas.base import AppBaseModel
from app.schemas.common import ResponseEnvelope


class HealthCheckResponseData(AppBaseModel):
    status: str = "ok"
    version: str = "1.0.0"
    database_connected: bool
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class HealthCheckResponse(ResponseEnvelope[HealthCheckResponseData]):
    pass
