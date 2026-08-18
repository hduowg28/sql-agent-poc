"""
app/repositories/customer_repository.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Repository layer cho thao tác truy vấn dữ liệu Customer với SQLAlchemy Session.
"""
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session
from app.models.customer import Customer


class CustomerRepository:
    """Repository quản lý CRUD cho bảng Customers."""

    @staticmethod
    def get_by_id(db: Session, customer_id: str) -> Customer | None:
        """Lấy thông tin Customer theo customer_id."""
        return db.query(Customer).filter(Customer.customer_id == customer_id).first()

    @staticmethod
    def exists_by_id(db: Session, customer_id: str) -> bool:
        """Kiểm tra xem customer_id đã tồn tại chưa."""
        return db.query(Customer.customer_id).filter(Customer.customer_id == customer_id).first() is not None

    @staticmethod
    def create(db: Session, customer: Customer) -> Customer:
        """Thêm một Customer mới vào database."""
        db.add(customer)
        db.commit()
        db.refresh(customer)
        return customer

    @staticmethod
    def execute_raw_sql(
        db: Session,
        sql: str,
        rollback_after_execution: bool = True,
    ) -> dict[str, Any]:

        sql = sql.strip()

        if not sql:
            raise ValueError("SQL query không được để trống.")

        try:
            result = db.execute(text(sql))

            # Lấy metadata trước rollback.
            row_count = result.rowcount

            rows = []

            if result.returns_rows:
                rows = [
                    dict(row._mapping)
                    for row in result.fetchall()
                ]

            # ================================================
            # LAB MODE:
            # luôn rollback sau execution
            # ================================================
            if rollback_after_execution:
                db.rollback()

                return {
                    "success": True,
                    "rolled_back": True,
                    "row_count": row_count,
                    "rows": rows,
                    "message": (
                        "SQL đã được thực thi trong laboratory "
                        "transaction và đã được ROLLBACK."
                    ),
                }

            # Chỉ dùng khi thực sự muốn persistence trong lab.
            db.commit()

            return {
                "success": True,
                "rolled_back": False,
                "row_count": row_count,
                "rows": rows,
                "message": "SQL đã được thực thi và COMMIT.",
            }

        except Exception as exc:
            db.rollback()

            return {
                "success": False,
                "rolled_back": True,
                "row_count": 0,
                "rows": [],
                "error": str(exc),
                "message": (
                    "SQL execution thất bại. "
                    "Transaction đã được ROLLBACK."
                ),
            }