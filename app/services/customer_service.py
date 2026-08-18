"""
app/services/customer_service.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Business Logic Layer cho thao tác liên quan tới Customer.
"""

import logging
import uuid
from sqlalchemy.orm import Session

from app.core.exceptions import (
    CustomerAlreadyExistsException,
    CustomerNotFoundException,
    ValidationException,
)
from app.models.customer import Customer
from app.repositories.customer_repository import CustomerRepository
from app.schemas.customer import CustomerCreate, CustomerResponse

logger = logging.getLogger(__name__)


class CustomerService:
    """Service xử lý logic cho Customer (get_customer, register_customer)."""

    @staticmethod
    def get_customer(db: Session, customer_id: str) -> CustomerResponse:
        """
        Truy xuất thông tin chi tiết của một khách hàng dựa trên customer_id.

        Args:
            db: SQLAlchemy Session.
            customer_id: Mã định danh khách hàng.

        Returns:
            CustomerResponse: Thông tin chi tiết khách hàng.

        Raises:
            ValidationException: Nếu customer_id rỗng.
            CustomerNotFoundException: Nếu không tìm thấy khách hàng.
        """
        clean_id = customer_id.strip() if customer_id else ""
        if not clean_id:
            raise ValidationException(
                field="customer_id",
                detail="Mã khách hàng không được để trống.",
            )

        customer = CustomerRepository.get_by_id(db, clean_id)
        if not customer:
            logger.warning(f"[CustomerService] Không tìm thấy khách hàng: {clean_id}")
            raise CustomerNotFoundException(customer_id=clean_id)

        logger.info(f"[CustomerService] Lấy thông tin khách hàng thành công: {clean_id}")
        return CustomerResponse.model_validate(customer)

    @staticmethod
    def register_customer(db: Session, request: CustomerCreate) -> CustomerResponse:
        """
        Đăng ký thông tin khách hàng mới vào hệ thống.

        Args:
            db: SQLAlchemy Session.
            request: Dữ liệu đăng ký từ CustomerCreate schema.

        Returns:
            CustomerResponse: Thông tin khách hàng vừa tạo thành công.

        Raises:
            ValidationException: Nếu dữ liệu không hợp lệ.
            CustomerAlreadyExistsException: Nếu customer_id đã tồn tại.
        """
        name = request.customer_name.strip() if request.customer_name else ""
        if not name:
            raise ValidationException(
                field="customer_name",
                detail="Tên khách hàng không được để trống.",
            )

        # Xử lý customer_id
        if request.customer_id and request.customer_id.strip():
            cid = request.customer_id.strip()
            if CustomerRepository.exists_by_id(db, cid):
                logger.warning(f"[CustomerService] Trùng mã khách hàng: {cid}")
                raise CustomerAlreadyExistsException(customer_id=cid)
        else:
            # Tự động tạo customer_id ngẫu nhiên nếu không cung cấp
            cid = f"CUST-{uuid.uuid4().hex[:8].upper()}"
            while CustomerRepository.exists_by_id(db, cid):
                cid = f"CUST-{uuid.uuid4().hex[:8].upper()}"

        customer = Customer(
            customer_id=cid,
            customer_name=name,
            segment=request.segment.strip() if request.segment else None,
            country=request.country.strip() if request.country else None,
            city=request.city.strip() if request.city else None,
            state=request.state.strip() if request.state else None,
            postal_code=request.postal_code.strip() if request.postal_code else None,
            region=request.region.strip() if request.region else None,
        )

        saved = CustomerRepository.create(db, customer)
        logger.info(f"[CustomerService] Đăng ký khách hàng thành công: customer_id={cid}, name='{name}'")
        return CustomerResponse.model_validate(saved)
