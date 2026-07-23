from typing import Any
from pydantic import Field
from app.schemas.base import AppBaseModel
from app.schemas.common import ResponseEnvelope


class SQLExecutionRequest(AppBaseModel):
    """Payload schema for direct SQL query execution / validation endpoints."""

    sql_query: str = Field(
        ...,
        min_length=5,
        max_length=5000,
        description="Raw SQL query string to validate or execute.",
        examples=["SELECT id, email FROM users LIMIT 10;"],
    )
    max_rows: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum row limit to safeguard memory consumption.",
    )
    timeout_seconds: float = Field(
        default=10.0,
        ge=0.5,
        le=60.0,
        description="Query execution timeout limit in seconds.",
    )


class SQLQueryResult(AppBaseModel):
    """Tabular query execution output payload."""

    columns: list[str] = Field(
        default_factory=list,
        description="List of column names returned by query.",
        examples=[["id", "email"]],
    )
    rows: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of row objects mapping column name to value.",
    )
    row_count: int = Field(
        ...,
        ge=0,
        description="Total row count returned.",
        examples=[10],
    )
    execution_time_ms: float = Field(
        ...,
        ge=0,
        description="Database query execution duration in milliseconds.",
        examples=[14.2],
    )


class ColumnSchemaInfo(AppBaseModel):
    """Database column metadata for schema introspection."""

    name: str = Field(..., description="Column name.")
    type: str = Field(..., description="Database column data type (e.g. VARCHAR, INTEGER).")
    nullable: bool = Field(default=True, description="Whether column accepts NULL values.")
    primary_key: bool = Field(default=False, description="Whether column is a primary key.")


class TableSchemaInfo(AppBaseModel):
    """Database table metadata for agent tools and schema exploration API."""

    table_name: str = Field(..., description="Table name in database.")
    columns: list[ColumnSchemaInfo] = Field(
        default_factory=list,
        description="List of table column definitions.",
    )
    row_count_estimate: int | None = Field(
        default=None,
        description="Estimated row count of the table.",
    )


class DatabaseSchemaResponse(ResponseEnvelope[list[TableSchemaInfo]]):
    """API response envelope for database schema exploration endpoint."""

    pass
