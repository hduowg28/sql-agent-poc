from typing import Any
from pydantic import Field
from app.schemas.base import AppBaseModel
from app.schemas.common import ResponseEnvelope


class SQLExecutionRequest(AppBaseModel):
    sql_query: str = Field(..., min_length=5, max_length=5000)
    max_rows: int = Field(default=100, ge=1, le=1000)
    timeout_seconds: float = Field(default=10.0, ge=0.5, le=60.0)


class SQLQueryResult(AppBaseModel):
    columns: list[str] = Field(default_factory=list)
    rows: list[dict[str, Any]] = Field(default_factory=list)
    row_count: int = Field(..., ge=0)
    execution_time_ms: float = Field(..., ge=0)


class ColumnSchemaInfo(AppBaseModel):
    name: str
    type: str
    nullable: bool = True
    primary_key: bool = False


class TableSchemaInfo(AppBaseModel):
    table_name: str
    columns: list[ColumnSchemaInfo] = Field(default_factory=list)
    row_count_estimate: int | None = None


class DatabaseSchemaResponse(ResponseEnvelope[list[TableSchemaInfo]]):
    pass
