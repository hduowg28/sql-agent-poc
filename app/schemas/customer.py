"""
app/schemas/customer.py
~~~~~~~~~~~~~~~~~~~~~~~~
Pydantic schemas cho Customer entity.
Inherit từ AppBaseModel để đảm bảo extra="forbid" và whitespace trimming tự động.
"""

from typing import Any
from pydantic import Field, field_validator
from app.schemas.base import AppBaseModel


class CustomerBase(AppBaseModel):
    customer_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Tên đầy đủ của khách hàng.",
        examples=["John Doe"],
    )
    segment: str | None = Field(
        default=None,
        max_length=100,
        description="Phân khúc khách hàng (Consumer, Corporate, Home Office).",
        examples=["Consumer"],
    )
    country: str | None = Field(
        default=None,
        max_length=100,
        description="Quốc gia của khách hàng.",
        examples=["United States"],
    )
    city: str | None = Field(
        default=None,
        max_length=100,
        description="Thành phố của khách hàng.",
        examples=["New York"],
    )
    state: str | None = Field(
        default=None,
        max_length=100,
        description="Bang / Tỉnh thành.",
        examples=["New York"],
    )
    postal_code: str | None = Field(
        default=None,
        max_length=50,
        description="Mã bưu chính.",
        examples=["10001"],
    )
    region: str | None = Field(
        default=None,
        max_length=100,
        description="Khu vực (East, West, Central, South).",
        examples=["East"],
    )

    @field_validator("postal_code", mode="before")
    @classmethod
    def coerce_postal_code_to_str(cls, v: Any) -> str | None:
        if v is not None:
            return str(v)
        return None


class CustomerCreate(CustomerBase):
    """Schema tạo mới Customer từ phía Client. Không chứa customer_id vì ID được sinh tự động."""
    pass


class CustomerResponse(CustomerBase):
    """Schema thông tin Customer đầy đủ trả về từ Server."""
    customer_id: str = Field(
        ...,
        description="Mã định danh duy nhất của khách hàng.",
        examples=["CUST-10001"],
    )
