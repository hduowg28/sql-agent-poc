from typing import TYPE_CHECKING, List
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.order import Order


class Customer(Base):
    """Customer entity representing e-commerce clients."""

    __tablename__ = "customers"

    customer_id: Mapped[str] = mapped_column(String(50), primary_key=True, index=True)
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    segment: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    region: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Relationships
    orders: Mapped[List["Order"]] = relationship(
        "Order", back_populates="customer", cascade="all, delete-orphan"
    )
