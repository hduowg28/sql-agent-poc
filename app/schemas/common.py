from typing import Any, Generic, TypeVar
from pydantic import Field
from app.schemas.base import AppBaseModel

DataT = TypeVar("DataT")


class ResponseEnvelope(AppBaseModel, Generic[DataT]):
    success: bool = True
    message: str = "Success"
    data: DataT | None = None
    meta: dict[str, Any] | None = None


class ErrorDetail(AppBaseModel):
    code: str
    message: str
    field: str | None = None


class ErrorResponse(AppBaseModel):
    success: bool = False
    error: str
    details: list[ErrorDetail] = Field(default_factory=list)
