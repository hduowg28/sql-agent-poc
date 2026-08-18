"""
app/api/customer.py
~~~~~~~~~~~~~~~~~~~
Customer API Router cho get_customer và register_customer.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import ResponseEnvelope
from app.schemas.customer import CustomerCreate, CustomerResponse
from app.services.customer_service import CustomerService

router = APIRouter(
    prefix="/customers",
    tags=["Customers"],
)


@router.get(
    "/{customer_id}",
    response_model=ResponseEnvelope[CustomerResponse],
    status_code=status.HTTP_200_OK,
    summary="Truy xuất thông tin chi tiết của một khách hàng (get_customer)",
    description="Lấy toàn bộ thông tin chi tiết của khách hàng dựa trên customer_id.",
)
def get_customer(
    customer_id: str,
    db: Session = Depends(get_db),
) -> ResponseEnvelope[CustomerResponse]:
    """
    Endpoint get_customer:
    - **customer_id**: Mã định danh khách hàng (ví dụ: 'CG-12520')
    """
    data = CustomerService.get_customer(db=db, customer_id=customer_id)
    return ResponseEnvelope[CustomerResponse](
        success=True,
        message="Truy xuất thông tin khách hàng thành công.",
        data=data,
    )


@router.post(
    "/register",
    response_model=ResponseEnvelope[CustomerResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Đăng ký thông tin khách hàng mới (register_customer)",
    description="Đăng ký thông tin khách hàng mới vào hệ thống cơ sở dữ liệu.",
)
def register_customer(
    request: CustomerCreate,
    db: Session = Depends(get_db),
) -> ResponseEnvelope[CustomerResponse]:
    """
    Endpoint register_customer:
    - **customer_id**: Mã định danh (tuỳ chọn)
    - **customer_name**: Tên khách hàng (bắt buộc)
    - các thông tin địa chỉ, khu vực, phân khúc (tuỳ chọn)
    """
    data = CustomerService.register_customer(db=db, request=request)
    return ResponseEnvelope[CustomerResponse](
        success=True,
        message="Đăng ký thông tin khách hàng mới thành công.",
        data=data,
    )
