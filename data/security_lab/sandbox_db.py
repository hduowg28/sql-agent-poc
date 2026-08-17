"""
data/security_lab/sandbox_db.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Database Sandbox Executor & SQL Classifier:
Thực thi SQL Query trong môi trường Sandbox cô lập ở mức DB Engine:
  1. Phân loại câu lệnh SQL (READ, WRITE, DELETE, DDL, DCL, OTHER).
  2. Mở connection riêng từ SQLAlchemy engine.
  3. Tùy chọn chế độ READ ONLY hoặc cho phép thực thi DML/DDL (UPDATE, DELETE, INSERT).
  4. Thực thi query truy vấn / chỉnh sửa dữ liệu.
  5. LUÔN khôi phục/hủy giao dịch (ROLLBACK) trong khối `finally` để không tác động vĩnh viễn tới DB.
"""

import re
import logging
from enum import Enum
from typing import Any
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, OperationalError, ProgrammingError, InternalError
from langchain_community.utilities import SQLDatabase

logger = logging.getLogger(__name__)


class SQLCategory(str, Enum):
    """Danh mục loại câu lệnh SQL."""
    READ = "READ"        # SELECT, WITH, EXPLAIN
    WRITE = "WRITE"      # INSERT, UPDATE, MERGE, UPSERT, REPLACE
    DELETE = "DELETE"    # DELETE, TRUNCATE
    DDL = "DDL"          # DROP, CREATE, ALTER, RENAME
    DCL = "DCL"          # GRANT, REVOKE
    OTHER = "OTHER"      # EXEC, CALL, COMMIT, ROLLBACK, v.v.


class DBSandboxError(Exception):
    """Ngoại lệ riêng cho cơ chế DB Sandbox khi phát hiện hành vi ghi/sửa dữ liệu trong chế độ READ ONLY."""
    def __init__(self, message: str = "Lỗi bảo mật (Sandbox DB): Thao tác bị từ chối bởi cơ chế Sandbox DB (READ ONLY mode)."):
        self.message = message
        super().__init__(message)


def classify_sql(query: str) -> SQLCategory:
    """
    Phân loại câu lệnh SQL dựa trên từ khóa đầu tiên (bỏ qua SQL comments).

    Category mapping:
      - SELECT, WITH, EXPLAIN, SHOW      -> READ
      - INSERT, UPDATE, MERGE, REPLACE   -> WRITE
      - DELETE, TRUNCATE                 -> DELETE
      - DROP, CREATE, ALTER, RENAME      -> DDL
      - GRANT, REVOKE                    -> DCL
      - Lệnh khác                        -> OTHER
    """
    if not query or not query.strip():
        return SQLCategory.OTHER

    # Loại bỏ comment kiểu inline (-- ...) và block (/* ... */)
    cleaned = re.sub(r"(/\*.*?\*/|--[^\r\n]*)", "", query, flags=re.DOTALL).strip()
    if not cleaned:
        return SQLCategory.OTHER

    # Lấy từ khóa chữ cái đầu tiên
    match = re.match(r"^([a-zA-Z]+)", cleaned)
    if not match:
        return SQLCategory.OTHER

    first_word = match.group(1).upper()

    if first_word in ("SELECT", "WITH", "EXPLAIN", "SHOW"):
        return SQLCategory.READ
    elif first_word in ("INSERT", "UPDATE", "MERGE", "UPSERT", "REPLACE"):
        return SQLCategory.WRITE
    elif first_word in ("DELETE", "TRUNCATE"):
        return SQLCategory.DELETE
    elif first_word in ("DROP", "CREATE", "ALTER", "RENAME"):
        return SQLCategory.DDL
    elif first_word in ("GRANT", "REVOKE"):
        return SQLCategory.DCL
    else:
        return SQLCategory.OTHER


def execute_sql_in_sandbox(db: SQLDatabase, query: str, read_only: bool = False) -> str:
    """
    Thực thi câu lệnh SQL trong môi trường Sandbox cô lập.

    Args:
        db: Đối tượng SQLDatabase của LangChain.
        query: Câu lệnh SQL cần thực thi.
        read_only: Nếu True, kích hoạt SET TRANSACTION READ ONLY. Nếu False, cho phép chạy UPDATE/DELETE/INSERT.

    Returns:
        Kết quả câu lệnh dưới dạng chuỗi string kèm phân loại Category.
    """
    cleaned_query = query.strip()
    if not cleaned_query:
        return "Query rỗng."

    category = classify_sql(cleaned_query)
    logger.info(f"[DBSandbox] Executing [{category.value}] query: {cleaned_query[:150]}")

    engine = db._engine

    with engine.connect() as conn:
        trans = conn.begin()
        try:
            # 1. Nếu bật read_only, áp dụng SET TRANSACTION READ ONLY trên PostgreSQL
            if read_only:
                try:
                    conn.execute(text("SET TRANSACTION READ ONLY;"))
                except Exception:
                    pass

            # 2. Thực thi câu lệnh SQL
            cursor_result = conn.execute(text(cleaned_query))

            # 3. Trả về kết quả phù hợp
            if cursor_result.returns_rows:
                rows = cursor_result.fetchall()
                result_list = [tuple(row) for row in rows]
                result_str = f"[{category.value}] {result_list}"
            else:
                result_str = f"[{category.value}] Execution successful in DB Sandbox. Rowcount affected: {cursor_result.rowcount}. (Note: Changes were automatically ROLLED BACK)."

            return result_str

        except (DBAPIError, OperationalError, ProgrammingError, InternalError) as db_err:
            err_text = str(db_err).lower()
            if read_only and any(kw in err_text for kw in [
                "read-only", "readonly", "cannot execute", "permission denied",
                "transaction is read-only", "modifying SQL data not permitted"
            ]):
                logger.warning(f"[DBSandbox] Thao tác [{category.value}] bị từ chối bởi Sandbox DB (READ ONLY): {db_err}")
                raise DBSandboxError(
                    f"Lỗi bảo mật (Sandbox DB): Câu lệnh [{category.value}] bị từ chối bởi chế độ giao dịch READ ONLY của Sandbox DB."
                )
            raise db_err

        finally:
            # 4. LUÔN ROLLBACK giao dịch để giữ an toàn cho dữ liệu gốc
            trans.rollback()
