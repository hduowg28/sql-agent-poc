"""
app/services/customer_service.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Business Logic layer cho Customer domain.
Thực thi validation kinh doanh, sinh customer_id tự động, gọi Repository layer.
"""

import uuid
import logging
from sqlalchemy.orm import Session
from app.repositories.customer_repository import CustomerRepository
from app.schemas.customer import CustomerCreate, CustomerResponse
from app.core.exceptions import (
    CustomerNotFoundException,
    CustomerAlreadyExistsException,
    ValidationException,
)

logger = logging.getLogger(__name__)


class CustomerService:
    @staticmethod
    def _generate_customer_id() -> str:
        """Sinh customer_id duy nhất định dạng CUST-XXXXXX (ví dụ: CUST-8F3A12)."""
        short_code = uuid.uuid4().hex[:6].upper()
        return f"CUST-{short_code}"

    @classmethod
    def get_customer(cls, customer_id: str, db: Session) -> CustomerResponse:
        """
        Lấy thông tin chi tiết của một Customer theo ID.

        Raises:
            ValidationException: Nếu customer_id rỗng.
            CustomerNotFoundException: Nếu không tìm thấy trong DB (HTTP 404).
        """
        customer_id = customer_id.strip() if customer_id else ""
        if not customer_id:
            raise ValidationException(field="customer_id", detail="Mã customer_id không được để trống.")

        repo = CustomerRepository(db)
        customer = repo.get_by_id(customer_id)

        if not customer:
            logger.warning(f"[CustomerService] Không tìm thấy customer: {customer_id}")
            raise CustomerNotFoundException(customer_id=customer_id)

        logger.info(f"[CustomerService] Lấy thành công customer: {customer_id}")
        return CustomerResponse.model_validate(customer)

    @classmethod
    def register_customer(cls, data: CustomerCreate, db: Session) -> CustomerResponse:
        """
        Đăng ký thông tin Customer mới vào hệ thống.

        Raises:
            CustomerAlreadyExistsException: Nếu trùng tên và thành phố.
        """
        repo = CustomerRepository(db)

        # 1. Kiểm tra trùng lặp cơ bản
        if repo.exists_by_name_and_city(data.customer_name, data.city):
            logger.warning(f"[CustomerService] Khách hàng trùng lặp: {data.customer_name} tại {data.city}")
            raise CustomerAlreadyExistsException(
                detail=f"Khách hàng '{data.customer_name}' tại thành phố '{data.city}' đã tồn tại."
            )

        # 2. Sinh customer_id duy nhất
        customer_id = cls._generate_customer_id()
        while repo.get_by_id(customer_id) is not None:
            customer_id = cls._generate_customer_id()

        # 3. Tạo record qua repository
        new_customer = repo.create(customer_id=customer_id, data=data)
        logger.info(f"[CustomerService] Đã đăng ký khách hàng mới thành công: {customer_id}")

        return CustomerResponse.model_validate(new_customer)
