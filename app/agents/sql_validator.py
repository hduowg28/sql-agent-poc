"""
app/agents/sql_validator.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Guard Layer: Kiểm tra và chặn các câu lệnh SQL nguy hiểm trước khi
truyền vào database hoặc LLM agent.

Nguyên tắc: chỉ cho phép SELECT. Mọi lệnh ghi (DML/DDL) đều bị từ chối.
"""
# dùng cơ chế guadrails // sử dụng prompt -> hacker sử dụng ngôn ngữ tự nhiên khác tiếng anh 


import re
import logging
from app.core.exceptions import SQLInjectionError

logger = logging.getLogger(__name__)

FORBIDDEN_KEYWORDS: list[str] = [
    # DML – ghi / xóa dữ liệu
    "INSERT",
    "UPDATE",
    "DELETE",
    "MERGE",
    "UPSERT",
    "REPLACE",
    # DDL – thay đổi cấu trúc
    "DROP",
    "CREATE",
    "ALTER",
    "TRUNCATE",
    "RENAME",
    # DCL – phân quyền
    "GRANT",
    "REVOKE",
    # TCL nguy hiểm
    "COMMIT",
    "ROLLBACK",
    "SAVEPOINT",
    # Lệnh DB đặc biệt
    "EXEC",
    "EXECUTE",
    "CALL",
    "COPY",
    "VACUUM",
    "ANALYZE",
    "EXPLAIN",   # optional: bật nếu muốn cho phép EXPLAIN
]

# Pre-compile regex một lần duy nhất để tái sử dụng
_FORBIDDEN_PATTERN: re.Pattern = re.compile(
    r"\b(" + "|".join(re.escape(kw) for kw in FORBIDDEN_KEYWORDS) + r")\b",
    flags=re.IGNORECASE,
)


def validate_sql(sql: str) -> str:
    """
    Kiểm tra câu lệnh SQL có chứa từ khoá nguy hiểm hay không.

    Args:
        sql: Câu lệnh SQL cần kiểm tra (thường là output của LLM).

    Returns:
        sql gốc (đã strip) nếu hợp lệ.

    Raises:
        SQLInjectionError: Nếu phát hiện từ khoá bị cấm.
    """
    cleaned = sql.strip()
    match = _FORBIDDEN_PATTERN.search(cleaned)
    if match:
        forbidden_kw = match.group(0).upper()
        logger.warning(
            "[SQLValidator] Phát hiện câu lệnh nguy hiểm. "
            f"Từ khoá bị cấm: '{forbidden_kw}'. SQL: {cleaned[:200]}"
        )
        raise SQLInjectionError(forbidden_keyword=forbidden_kw)

    logger.debug(f"[SQLValidator] SQL hợp lệ: {cleaned[:200]}")
    return cleaned


def is_safe_sql(sql: str) -> bool:
    """
    Phiên bản boolean của validate_sql – không raise exception.
    Dùng tiện lợi trong các guard check nhanh.

    Returns:
        True nếu an toàn, False nếu phát hiện từ khoá nguy hiểm.
    """
    try:
        validate_sql(sql)
        return True
    except SQLInjectionError:
        return False
