"""
app/agents/tools.py
~~~~~~~~~~~~~~~~~~~
Custom LangChain Tools cho SQL Agent.

Tool duy nhất hiện tại:
    - SafeSQLQueryTool: Thực thi SELECT query qua SQLDatabase sau khi đã
      pass qua sql_validator guard. Read-only, có timeout.
"""

import logging
import signal
import platform
from typing import Any

from langchain.tools import BaseTool
from langchain_community.utilities import SQLDatabase
from pydantic import Field

from data.security_lab.sandbox_db import execute_sql_in_sandbox, DBSandboxError
from app.agents.sql_validator import validate_sql
from app.core.exceptions import AgentTimeoutError, SQLInjectionError

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
    """
    LangChain Tool thực thi câu lệnh SQL qua Sandbox DB:
      1. Thực thi query (SELECT, UPDATE, DELETE, INSERT) trong Sandbox DB cô lập.
      2. Tự động ROLLBACK sau khi chạy để đảm bảo an toàn cho dữ liệu thật.
      3. Áp dụng giới hạn timeout.
    """

    name: str = "sql_query"
    description: str = (
        "Thực thi câu lệnh SQL (SELECT, UPDATE, DELETE, INSERT, v.v.) để truy vấn hoặc thử nghiệm thay đổi dữ liệu. "
        "Chạy trong môi trường Sandbox DB an toàn cô lập (mọi thay đổi sẽ tự động rollback). "
        "Input: một câu lệnh SQL hợp lệ. "
        "Output: kết quả truy vấn hoặc số dòng bị ảnh hưởng dưới dạng text."
    )
    db: SQLDatabase = Field(exclude=True)
    timeout_seconds: int = Field(default=_DEFAULT_TIMEOUT_SECONDS)

    class Config:
        arbitrary_types_allowed = True

    def _run(self, query: str, **kwargs: Any) -> str:
        """Thực thi query qua cơ chế DB Sandbox."""
        try:
            validated_query = validate_sql(query)
        except SQLInjectionError as exc:
            logger.error(f"[SQLQueryTool] SQL bị từ chối: {exc}")
            return f" Lỗi bảo mật: {exc.message}"

        logger.info(f"[SQLQueryTool] Thực thi query qua Sandbox DB: {validated_query[:200]}")
        try:
            result = _run_with_timeout(
                execute_sql_in_sandbox,
                self.db,
                validated_query,
                timeout=self.timeout_seconds,
            )
            logger.info("[SQLQueryTool] Query Sandbox thực thi thành công.")
            return str(result)
        except DBSandboxError as exc:
            logger.error(f"[SQLQueryTool] Lỗi bảo mật Sandbox DB: {exc}")
            return f" Lỗi bảo mật: {exc.message}"
        except AgentTimeoutError as exc:
            logger.error(f"[SQLQueryTool] Timeout: {exc}")
            return f"⏱️ Lỗi timeout: Query vượt quá {self.timeout_seconds}s."
        except Exception as exc:
            logger.error(f"[SQLQueryTool] Lỗi thực thi query: {exc}")
            return f" Lỗi thực thi query: {exc}"

    async def _arun(self, query: str, **kwargs: Any) -> str:
        """Async version – delegate về _run."""
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


class GetCustomerTool(BaseTool):
    """
    LangChain Custom Tool lấy thông tin chi tiết một Customer qua Business Service.
    """

    name: str = "get_customer"
    description: str = (
        "Lấy thông tin chi tiết của một khách hàng dựa trên customer_id (ví dụ: 'CG-12520' hoặc 'CUST-001'). "
        "Input: mã customer_id duy nhất dưới dạng string."
    )
    db: SQLDatabase = Field(exclude=True)

    class Config:
        arbitrary_types_allowed = True

    def _run(self, customer_id: str, **kwargs: Any) -> str:
        if not customer_id or not isinstance(customer_id, str) or not customer_id.strip():
            return "Vui lòng cung cấp mã customer_id hợp lệ."
        try:
            from app.core.database import SessionLocal
            from app.services.customer_service import CustomerService

            with SessionLocal() as db_session:
                res = CustomerService.get_customer(customer_id=customer_id.strip(), db=db_session)
                return str(res.model_dump())
        except Exception as exc:
            logger.error(f"[GetCustomerTool] Lỗi khi lấy thông tin customer '{customer_id}': {exc}")
            return f" Lỗi khi lấy thông tin customer: {exc}"

    async def _arun(self, customer_id: str, **kwargs: Any) -> str:
        return self._run(customer_id, **kwargs)


class RegisterCustomerTool(BaseTool):
    """
    LangChain Custom Tool đăng ký thông tin Customer mới qua Business Service.
    """

    name: str = "register_customer"
    description: str = (
        "Đăng ký một thông tin khách hàng mới vào hệ thống. "
        "Input: customer_name (bắt buộc), segment, country, city, state, postal_code, region."
    )
    db: SQLDatabase = Field(exclude=True)

    class Config:
        arbitrary_types_allowed = True

    def _run(self, tool_input: str | dict, **kwargs: Any) -> str:
        try:
            import json
            from app.core.database import SessionLocal
            from app.schemas.customer import CustomerCreate
            from app.services.customer_service import CustomerService

            data_dict = {}
            if isinstance(tool_input, dict):
                data_dict = tool_input
            elif isinstance(tool_input, str):
                cleaned = tool_input.strip()
                if cleaned.startswith("{") and cleaned.endswith("}"):
                    data_dict = json.loads(cleaned)
                else:
                    parts = [p.strip() for p in cleaned.split(",") if ":" in p]
                    for part in parts:
                        k, v = part.split(":", 1)
                        data_dict[k.strip()] = v.strip()
                    if "customer_name" not in data_dict and cleaned:
                        data_dict["customer_name"] = cleaned

            create_schema = CustomerCreate(**data_dict)
            with SessionLocal() as db_session:
                res = CustomerService.register_customer(data=create_schema, db=db_session)
                return f"Đăng ký khách hàng thành công: {res.model_dump()}"

        except Exception as exc:
            logger.error(f"[RegisterCustomerTool] Lỗi đăng ký customer: {exc}")
            return f" Lỗi đăng ký customer: {exc}"

    async def _arun(self, tool_input: str | dict, **kwargs: Any) -> str:
        return self._run(tool_input, **kwargs)