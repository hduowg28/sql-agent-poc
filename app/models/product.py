from typing import TYPE_CHECKING, List
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.order import Order


class Product(Base):
    """Product entity representing catalog items."""

    __tablename__ = "products"

    product_id: Mapped[str] = mapped_column(String(100), primary_key=True, index=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sub_category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    product_name: Mapped[str] = mapped_column(String(500), nullable=False)

    # Relationships
    orders: Mapped[List["Order"]] = relationship(
        "Order", back_populates="product", cascade="all, delete-orphan"
    )
