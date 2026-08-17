"""
app/repositories/customer_repository.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Repository layer quản lý các thao tác tương tác DB trực tiếp cho Customer entity.
Sử dụng SQLAlchemy Session được truyền vào qua Dependency Injection.
"""

import logging
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.customer import Customer
from app.schemas.customer import CustomerCreate

logger = logging.getLogger(__name__)


class CustomerRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, customer_id: str) -> Customer | None:
        """Lấy Customer theo primary key customer_id."""
        stmt = select(Customer).where(Customer.customer_id == customer_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def exists_by_name_and_city(self, customer_name: str, city: str | None) -> bool:
        """Kiểm tra xem khách hàng có cùng tên và thành phố đã tồn tại hay chưa."""
        stmt = select(Customer).where(Customer.customer_name == customer_name)
        if city:
            stmt = stmt.where(Customer.city == city)
        result = self.db.execute(stmt).scalars().first()
        return result is not None

    def create(self, customer_id: str, data: CustomerCreate) -> Customer:
        """Tạo Customer mới và lưu vào database trong giao dịch."""
        customer = Customer(
            customer_id=customer_id,
            customer_name=data.customer_name,
            segment=data.segment,
            country=data.country,
            city=data.city,
            state=data.state,
            postal_code=data.postal_code,
            region=data.region,
        )
        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)
        logger.info(f"[CustomerRepository] Đã tạo Customer thành công: {customer_id}")
        return customer
