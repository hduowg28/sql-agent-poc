"""
app/core/exceptions.py
~~~~~~~~~~~~~~~~~~~~~~
Custom exceptions cho toàn bộ ứng dụng.

Hierarchy:
    AppException (base)
    ├── DatabaseException
    │   ├── ConnectionError
    │   ├── QueryError
    │   └── UploadError
    ├── AgentException
    │   ├── SQLInjectionError
    │   └── AgentTimeoutError
    └── ValidationException
"""

class AppException(Exception):
    """Base exception cho mọi lỗi trong ứng dụng."""

    def __init__(self, message: str, detail: str | None = None) -> None:
        self.message = message
        self.detail = detail
        super().__init__(message)

    def __str__(self) -> str:
        if self.detail:
            return f"{self.message} | Detail: {self.detail}"
        return self.message

class DatabaseException(AppException):
    """Base exception cho mọi lỗi liên quan đến database."""


class DatabaseConnectionError(DatabaseException):
    """Không thể kết nối đến database."""

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(
            message="Không thể kết nối đến database.",
            detail=detail,
        )


class DatabaseQueryError(DatabaseException):
    """Lỗi xảy ra khi thực thi SQL query."""

    def __init__(self, query: str | None = None, detail: str | None = None) -> None:
        self.query = query
        super().__init__(
            message="Lỗi khi thực thi câu truy vấn SQL.",
            detail=detail,
        )


class DatabaseUploadError(DatabaseException):
    """Lỗi xảy ra trong quá trình ETL / upload dữ liệu."""

    def __init__(self, table: str | None = None, detail: str | None = None) -> None:
        self.table = table
        super().__init__(
            message=f"Lỗi khi tải dữ liệu lên bảng '{table}'." if table else "Lỗi khi tải dữ liệu.",
            detail=detail,
        )


class AgentException(AppException):
    """Base exception cho mọi lỗi liên quan đến SQL Agent."""


class SQLInjectionError(AgentException):
    """Câu lệnh SQL chứa lệnh nguy hiểm (DROP, DELETE, INSERT, ...)."""

    def __init__(self, forbidden_keyword: str | None = None) -> None:
        self.forbidden_keyword = forbidden_keyword
        super().__init__(
            message="Câu lệnh SQL bị từ chối vì chứa lệnh nguy hiểm.",
            detail=f"Từ khoá bị cấm: '{forbidden_keyword}'" if forbidden_keyword else None,
        )


class AgentTimeoutError(AgentException):
    """Agent vượt quá thời gian xử lý cho phép."""

    def __init__(self, timeout_seconds: int | None = None) -> None:
        super().__init__(
            message="Agent đã vượt quá thời gian xử lý.",
            detail=f"Timeout: {timeout_seconds}s" if timeout_seconds else None,
        )


class ValidationException(AppException):
    """Dữ liệu đầu vào không hợp lệ."""

    def __init__(self, field: str | None = None, detail: str | None = None) -> None:
        self.field = field
        super().__init__(
            message=f"Dữ liệu trường '{field}' không hợp lệ." if field else "Dữ liệu không hợp lệ.",
            detail=detail,
        )


class CustomerNotFoundException(ValidationException):
    """Không tìm thấy thông tin khách hàng."""

    def __init__(self, customer_id: str) -> None:
        self.customer_id = customer_id
        super().__init__(
            field="customer_id",
            detail=f"Không tìm thấy khách hàng với mã '{customer_id}'.",
        )


class CustomerAlreadyExistsException(ValidationException):
    """Khách hàng đã tồn tại trong hệ thống."""

    def __init__(self, detail: str) -> None:
        super().__init__(
            field="customer_name",
            detail=detail,
        )
