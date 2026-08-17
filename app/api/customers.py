"""
app/api/customers.py
~~~~~~~~~~~~~~~~~~~~
Customer REST API Router.

Endpoints:
  - GET  /api/customers/{customer_id} : Lấy thông tin chi tiết một Customer
  - POST /api/customers               : Đăng ký một Customer mới
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.customer import CustomerCreate, CustomerResponse
from app.services.customer_service import CustomerService

router = APIRouter(
    prefix="/customers",
    tags=["Customers"],
)


@router.get(
    "/{customer_id}",
    response_model=CustomerResponse,
    status_code=status.HTTP_200_OK,
    summary="Lấy thông tin Customer theo ID",
    description="Tra cứu và trả về thông tin chi tiết của một Customer dựa trên mã customer_id.",
)
def get_customer_by_id(
    customer_id: str,
    db: Session = Depends(get_db),
) -> CustomerResponse:
    """
    Lấy chi tiết thông tin khách hàng:
    - **customer_id**: Mã định danh của khách hàng (ví dụ: 'CG-12520' hoặc 'CUST-8F3A12')
    """
    return CustomerService.get_customer(customer_id=customer_id, db=db)


@router.post(
    "",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Đăng ký Customer mới",
    description="Đăng ký một thông tin khách hàng mới vào hệ thống. Backend tự động sinh mã customer_id.",
)
def register_customer(
    request: CustomerCreate,
    db: Session = Depends(get_db),
) -> CustomerResponse:
    """
    Đăng ký khách hàng mới:
    - **customer_name**: Tên đầy đủ của khách hàng (bắt buộc)
    - Các thông tin địa lý và phân khúc khác (tùy chọn)
    """
    return CustomerService.register_customer(data=request, db=db)
