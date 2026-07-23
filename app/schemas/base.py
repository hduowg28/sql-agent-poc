from datetime import datetime, timezone
from pydantic import BaseModel, ConfigDict, Field


class AppBaseModel(BaseModel):
    """
    Base model enforcing enterprise Pydantic v2 configurations across all application schemas.

    Config:
        str_strip_whitespace: Trims leading/trailing whitespace automatically.
        validate_assignment: Enforces model validation when mutating attributes.
        extra: Disallows unknown/unparsed payload fields to enforce clean API contracts.
        from_attributes: Enables ORM compatibility (converting ORM objects to schemas).
        populate_by_name: Allows populating fields by field name or alias (e.g. camelCase).
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
        from_attributes=True,
        populate_by_name=True,
    )


class TimestampMixin(BaseModel):
    """Mixin for models requiring audit timestamp tracking."""

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when the record was created.",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when the record was last updated.",
    )
