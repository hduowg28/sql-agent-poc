"""
app/schemas/customer.py
~~~~~~~~~~~~~~~~~~~~~~~
Pydantic schemas cho domain Customer.
"""

from typing import Any
from pydantic import Field, field_validator
from app.schemas.base import AppBaseModel


class CustomerCreate(AppBaseModel):
    """Schema dữ liệu đầu vào khi đăng ký khách hàng mới (register_customer)."""

    customer_id: str | None = Field(
        default=None,
        description="Mã định danh khách hàng (nếu không nhập sẽ tự động khởi tạo).",
        examples=["CUST-10001"],
    )
    customer_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Tên khách hàng.",
        examples=["Nguyen Van A"],
    )
    segment: str | None = Field(
        default=None,
        max_length=100,
        description="Phân khúc khách hàng (Consumer, Corporate, Home Office...).",
        examples=["Consumer"],
    )
    country: str | None = Field(
        default=None,
        max_length=100,
        description="Quốc gia.",
        examples=["Vietnam"],
    )
    city: str | None = Field(
        default=None,
        max_length=100,
        description="Thành phố.",
        examples=["Ho Chi Minh"],
    )
    state: str | None = Field(
        default=None,
        max_length=100,
        description="Bang / Tỉnh.",
        examples=["Ho Chi Minh"],
    )
    postal_code: str | None = Field(
        default=None,
        max_length=50,
        description="Mã bưu chính.",
        examples=["700000"],
    )
    region: str | None = Field(
        default=None,
        max_length=100,
        description="Khu vực.",
        examples=["South"],
    )

    @field_validator("postal_code", mode="before")
    @classmethod
    def coerce_postal_code(cls, v: Any) -> str | None:
        if v is None:
            return None
        if isinstance(v, float) and v.is_integer():
            return str(int(v))
        return str(v).strip() if str(v).strip() else None


class CustomerResponse(AppBaseModel):
    """Schema dữ liệu trả về thông tin chi tiết khách hàng (get_customer / register_customer)."""

    customer_id: str = Field(..., description="Mã định danh khách hàng.")
    customer_name: str = Field(..., description="Tên khách hàng.")
    segment: str | None = Field(default=None, description="Phân khúc khách hàng.")
    country: str | None = Field(default=None, description="Quốc gia.")
    city: str | None = Field(default=None, description="Thành phố.")
    state: str | None = Field(default=None, description="Bang / Tỉnh.")
    postal_code: str | None = Field(default=None, description="Mã bưu chính.")
    region: str | None = Field(default=None, description="Khu vực.")

    @field_validator("postal_code", mode="before")
    @classmethod
    def coerce_postal_code(cls, v: Any) -> str | None:
        if v is None:
            return None
        if isinstance(v, float) and v.is_integer():
            return str(int(v))
        return str(v).strip() if str(v).strip() else None
