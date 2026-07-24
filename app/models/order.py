from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.product import Product


class Order(Base):
    """Order transaction entity linking customers and products."""

    __tablename__ = "orders"

    row_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    order_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    ship_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ship_mode: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Foreign Keys
    customer_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("customers.customer_id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("products.product_id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Metrics
    sales: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    discount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    profit: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="orders")
    product: Mapped["Product"] = relationship("Product", back_populates="orders")

    __table_args__ = (
        Index("idx_orders_customer_product", "customer_id", "product_id"),
    )
