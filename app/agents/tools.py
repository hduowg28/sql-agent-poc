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

from app.agents.sql_validator import validate_sql
from app.core.exceptions import AgentTimeoutError, SQLInjectionError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Timeout helper (cross-platform)
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# SafeSQLQueryTool
# ---------------------------------------------------------------------------
class SafeSQLQueryTool(BaseTool):
    """
    LangChain Tool thực thi SQL SELECT an toàn:
      1. Validate SQL qua sql_validator (chặn DML/DDL)
      2. Chạy query qua SQLDatabase với timeout
      3. Trả về kết quả dạng string cho LLM xử lý tiếp
    """

    name: str = "sql_query"
    description: str = (
        "Thực thi một câu lệnh SQL SELECT để truy vấn dữ liệu từ database. "
        "Chỉ chấp nhận câu lệnh SELECT. "
        "Input: một câu lệnh SQL hợp lệ. "
        "Output: kết quả dạng bảng dưới dạng text."
    )
    db: SQLDatabase = Field(exclude=True)
    timeout_seconds: int = Field(default=_DEFAULT_TIMEOUT_SECONDS)

    class Config:
        arbitrary_types_allowed = True

    def _run(self, query: str, **kwargs: Any) -> str:
        """Thực thi query sau khi đã validate."""
        # 1. Guard: chặn câu lệnh nguy hiểm
        try:
            safe_query = validate_sql(query)
        except SQLInjectionError as exc:
            logger.error(f"[SafeSQLQueryTool] SQL bị từ chối: {exc}")
            return f"❌ Lỗi bảo mật: {exc.message}"

        # 2. Thực thi với timeout
        logger.info(f"[SafeSQLQueryTool] Thực thi query: {safe_query[:200]}")
        try:
            result = _run_with_timeout(
                self.db.run,
                safe_query,
                timeout=self.timeout_seconds,
            )
            logger.info("[SafeSQLQueryTool] Query thực thi thành công.")
            return str(result)
        except AgentTimeoutError as exc:
            logger.error(f"[SafeSQLQueryTool] Timeout: {exc}")
            return f"⏱️ Lỗi timeout: Query vượt quá {self.timeout_seconds}s."
        except Exception as exc:
            logger.error(f"[SafeSQLQueryTool] Lỗi không xác định: {exc}")
            return f"❌ Lỗi thực thi query: {exc}"

    async def _arun(self, query: str, **kwargs: Any) -> str:
        """Async version – delegate về _run (đủ dùng cho POC)."""
        return self._run(query, **kwargs)
