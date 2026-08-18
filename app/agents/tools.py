"""
app/agents/tools.py
~~~~~~~~~~~~~~~~~~~
Custom LangChain Tools cho SQL Agent.

Tool duy nhất hiện tại:
    - SQLQueryTool: Thực thi SELECT query qua SQLDatabase sau khi đã
      pass qua sql_validator guard. Read-only, có timeout.
"""

import logging
import signal
import platform
from typing import Any

from langchain.tools import BaseTool
from langchain_community.utilities import SQLDatabase
from pydantic import BaseModel, Field
from app.core.database import SessionLocal

from sqlalchemy import text
from app.agents.sql_validator import validate_sql
from app.core.exceptions import AgentTimeoutError, SQLInjectionError
from app.repositories.customer_repository import CustomerRepository

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT_SECONDS = 30

def _run_with_timeout(fn, *args, timeout: int = _DEFAULT_TIMEOUT_SECONDS, **kwargs) -> Any:
    """
    Chạy fn(*args, **kwargs) với giới hạn thời gian.
    - Unix  : dùng signal.SIGALRM (chính xác nhất)
    - Windows: dùng threading.Timer (fallback)
    """
    if platform.system() != "Windows":
        # --- Unix path ---
        def _handler(signum, frame):
            raise AgentTimeoutError(timeout_seconds=timeout)

        old = signal.signal(signal.SIGALRM, _handler)
        signal.alarm(timeout)
        try:
            return fn(*args, **kwargs)
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old)
    else:
        # --- Windows path: dùng concurrent.futures ---
        from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(fn, *args, **kwargs)
            try:
                return future.result(timeout=timeout)
            except FuturesTimeout:
                raise AgentTimeoutError(timeout_seconds=timeout)

class SQLQueryTool(BaseTool):
    name: str = "sql_query"

    description: str = (
        "Thực thi SQL query trên database. "
        "Trong vulnerable lab mode, có thể thực thi cả SELECT, INSERT, "
        "UPDATE, DELETE, DROP, ALTER và các câu lệnh SQL khác."
    )

    db: SQLDatabase = Field(exclude=True)
    timeout_seconds: int = Field(default=_DEFAULT_TIMEOUT_SECONDS)
    vulnerable_mode: bool = False

    class Config:
        arbitrary_types_allowed = True

    def _run(self, query: str, **kwargs: Any) -> str:
        query = query.strip()

        if not query:
            return "Lỗi: SQL query không được để trống."

        # ============================================================
        # SAFE MODE
        # ============================================================
        if not self.vulnerable_mode:
            try:
                query = validate_sql(query)

            except SQLInjectionError as exc:
                logger.error(
                    f"[SQLQueryTool] SQL bị từ chối: {exc}"
                )
                return f"Lỗi bảo mật: {exc.message}"

            try:
                result = _run_with_timeout(
                    self.db.run,
                    query,
                    timeout=self.timeout_seconds,
                )

                return str(result)

            except AgentTimeoutError as exc:
                logger.error(
                    f"[SQLQueryTool] Timeout: {exc}"
                )
                return f"Query vượt quá {self.timeout_seconds}s."

            except Exception as exc:
                logger.error(
                    f"[SQLQueryTool] SQL execution error: {exc}"
                )
                return f"Lỗi thực thi SQL: {exc}"

        # ============================================================
        # VULNERABLE LAB MODE
        # ============================================================

        logger.warning(
            "[VULNERABLE MODE] SQL validator BYPASSED. "
            f"Executing raw SQL: {query[:500]}"
        )

        db = SessionLocal()

        try:
            result = db.execute(text(query))

            # Lấy kết quả trước khi rollback.
            rows = []

            if result.returns_rows:
                rows = [
                    dict(row._mapping)
                    for row in result.fetchall()
                ]

            row_count = result.rowcount

            # LAB SAFETY:
            # rollback toàn bộ transaction sau testcase
            db.rollback()

            logger.warning(
                "[VULNERABLE MODE] SQL executed successfully "
                "but transaction was ROLLED BACK."
            )

            return str({
                "success": True,
                "vulnerable_mode": True,
                "rolled_back": True,
                "row_count": row_count,
                "rows": rows,
            })

        except Exception as exc:
            db.rollback()

            logger.error(
                f"[VULNERABLE MODE] SQL execution error: {exc}"
            )

            return str({
                "success": False,
                "vulnerable_mode": True,
                "rolled_back": True,
                "error": str(exc),
            })

        finally:
            db.close()

        async def _arun(self, query: str, **kwargs: Any) -> str:
            return self._run(query, **kwargs)


SafeSQLQueryTool = SQLQueryTool

class ListTablesTool(BaseTool):
    """
    LangChain Custom Tool liệt kê danh sách tất cả các bảng hiện có trong DB.
    Thay thế cho sql_db_list_tables của SQLDatabaseToolkit.
    """

    name: str = "list_tables"
    description: str = "Liệt kê danh sách tất cả các bảng hiện có trong cơ sở dữ liệu."
    db: SQLDatabase = Field(exclude=True)

    class Config:
        arbitrary_types_allowed = True

    def _run(self, tool_input: str = "", **kwargs: Any) -> str:
        try:
            tables = self.db.get_usable_table_names()
            return f"Các bảng hiện có trong cơ sở dữ liệu: {', '.join(tables)}"
        except Exception as exc:
            logger.error(f"[ListTablesTool] Lỗi khi lấy danh sách bảng: {exc}")
            return f"Lỗi khi lấy danh sách bảng: {exc}"

    async def _arun(self, tool_input: str = "", **kwargs: Any) -> str:
        return self._run(tool_input, **kwargs)

class GetTableSchemaTool(BaseTool):
    """
    LangChain Custom Tool lấy thông tin DDL schema và vài dòng mẫu của các bảng.
    Thay thế cho sql_db_schema của SQLDatabaseToolkit.
    """

    name: str = "get_table_schema"
    description: str = (
        "Lấy cấu trúc schema, tên cột, kiểu dữ liệu và một vài dòng mẫu của các bảng. "
        "Input: tên các bảng phân cách bằng dấu phẩy, ví dụ: 'customers, orders'."
    )
    db: SQLDatabase = Field(exclude=True)

    class Config:
        arbitrary_types_allowed = True

    def _run(self, table_names: str, **kwargs: Any) -> str:
        if not table_names or not table_names.strip():
            return " Vui lòng cung cấp tên các bảng cần xem schema (ví dụ: 'customers, orders')."

        tables = [t.strip() for t in table_names.split(",") if t.strip()]
        try:
            schema_info = self.db.get_table_info(tables)
            return schema_info
        except Exception as exc:
            logger.error(f"[GetTableSchemaTool] Lỗi khi lấy schema cho {table_names}: {exc}")
            return f"Lỗi khi lấy schema: {exc}"

    async def _arun(self, table_names: str, **kwargs: Any) -> str:
        return self._run(table_names, **kwargs)


class GetCustomerInput(BaseModel):
    customer_id: str = Field(description="Mã định danh khách hàng cần truy xuất (ví dụ: 'CG-12520')")


class GetCustomerTool(BaseTool):
    """
    LangChain Tool cho phép AI Agent lấy thông tin chi tiết của khách hàng theo customer_id.
    """

    name: str = "get_customer"
    description: str = (
        "Truy xuất thông tin chi tiết của một khách hàng từ cơ sở dữ liệu dựa trên customer_id. "
        "Dùng tool này khi người dùng hỏi thông tin cá nhân/địa chỉ/phân khúc của một khách hàng cụ thể theo mã customer_id."
    )
    args_schema: type[BaseModel] = GetCustomerInput

    def _run(self, customer_id: str, **kwargs: Any) -> str:
        from app.core.database import SessionLocal
        from app.core.exceptions import AppException
        from app.services.customer_service import CustomerService

        with SessionLocal() as db:
            try:
                res = CustomerService.get_customer(db=db, customer_id=customer_id)
                return (
                    f"Thông tin khách hàng {res.customer_id}:\n"
                    f"- Tên: {res.customer_name}\n"
                    f"- Phân khúc: {res.segment or 'N/A'}\n"
                    f"- Quốc gia: {res.country or 'N/A'}\n"
                    f"- Thành phố: {res.city or 'N/A'}\n"
                    f"- Bang/Tỉnh: {res.state or 'N/A'}\n"
                    f"- Mã bưu chính: {res.postal_code or 'N/A'}\n"
                    f"- Khu vực: {res.region or 'N/A'}"
                )
            except AppException as exc:
                return f"Không thể lấy thông tin khách hàng: {exc.message}"
            except Exception as exc:
                logger.error(f"[GetCustomerTool] Lỗi: {exc}")
                return f"Lỗi hệ thống khi lấy thông tin khách hàng: {exc}"

    async def _arun(self, customer_id: str, **kwargs: Any) -> str:
        return self._run(customer_id, **kwargs)


class RegisterCustomerInput(BaseModel):
    customer_name: str = Field(description="Tên đầy đủ của khách hàng (bắt buộc).")
    customer_id: str | None = Field(default=None, description="Mã định danh khách hàng (tuỳ chọn, ví dụ: 'CUST-10001').")
    segment: str | None = Field(default=None, description="Phân khúc khách hàng (ví dụ: 'Consumer', 'Corporate').")
    country: str | None = Field(default=None, description="Quốc gia.")
    city: str | None = Field(default=None, description="Thành phố.")
    state: str | None = Field(default=None, description="Bang/Tỉnh.")
    postal_code: str | None = Field(default=None, description="Mã bưu chính.")
    region: str | None = Field(default=None, description="Khu vực (ví dụ: 'South', 'East').")


class RegisterCustomerTool(BaseTool):
    """
    LangChain Tool cho phép AI Agent đăng ký thông tin khách hàng mới vào hệ thống DB.
    """

    name: str = "register_customer"
    description: str = (
        "Đăng ký thông tin khách hàng mới vào hệ thống database. "
        "Dùng tool này khi người dùng muốn thêm mới, khởi tạo hoặc đăng ký một khách hàng mới."
    )
    args_schema: type[BaseModel] = RegisterCustomerInput

    def _run(
        self,
        customer_name: str,
        customer_id: str | None = None,
        segment: str | None = None,
        country: str | None = None,
        city: str | None = None,
        state: str | None = None,
        postal_code: str | None = None,
        region: str | None = None,
        **kwargs: Any,
    ) -> str:
        from app.core.database import SessionLocal
        from app.core.exceptions import AppException
        from app.schemas.customer import CustomerCreate
        from app.services.customer_service import CustomerService

        req = CustomerCreate(
            customer_id=customer_id,
            customer_name=customer_name,
            segment=segment,
            country=country,
            city=city,
            state=state,
            postal_code=postal_code,
            region=region,
        )
        with SessionLocal() as db:
            try:
                res = CustomerService.register_customer(db=db, request=req)
                return (
                    f"Đăng ký khách hàng thành công!\n"
                    f"- Mã khách hàng: {res.customer_id}\n"
                    f"- Tên khách hàng: {res.customer_name}\n"
                    f"- Phân khúc: {res.segment or 'N/A'}\n"
                    f"- Thành phố: {res.city or 'N/A'}\n"
                    f"- Quốc gia: {res.country or 'N/A'}"
                )
            except AppException as exc:
                return f"Đăng ký khách hàng thất bại: {exc.message}"
            except Exception as exc:
                logger.error(f"[RegisterCustomerTool] Lỗi: {exc}")
                return f"Lỗi hệ thống khi đăng ký khách hàng: {exc}"

    async def _arun(
        self,
        customer_name: str,
        customer_id: str | None = None,
        segment: str | None = None,
        country: str | None = None,
        city: str | None = None,
        state: str | None = None,
        postal_code: str | None = None,
        region: str | None = None,
        **kwargs: Any,
    ) -> str:
        return self._run(
            customer_name=customer_name,
            customer_id=customer_id,
            segment=segment,
            country=country,
            city=city,
            state=state,
            postal_code=postal_code,
            region=region,
            **kwargs,
        )

class RawSQLInput(BaseModel):
    query: str = Field(
        description="SQL query dùng trong vulnerable security laboratory."
    )


class VulnerableSQLTool(BaseTool):
    """
    SQL execution tool dành riêng cho vulnerable security laboratory.

    Không sử dụng trong production.
    """

    name: str = "vulnerable_sql_query"

    description: str = (
        "Thực thi raw SQL trực tiếp trên database laboratory. "
        "Lab mode cho phép các câu lệnh SQL khác nhau. "
        "Sau execution transaction sẽ được rollback."
    )

    args_schema: type[BaseModel] = RawSQLInput

    def _run(self, query: str, **kwargs) -> str:
        with SessionLocal() as db:
            result = CustomerRepository.execute_raw_sql(
                db=db,
                sql=query,
                rollback_after_execution=True,
            )

            return str(result)

    async def _arun(
        self,
        query: str,
        **kwargs,
    ) -> str:
        return self._run(query=query, **kwargs)