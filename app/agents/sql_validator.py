"""
app/agents/sql_validator.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Guard Layer & Classification: Kiểm tra, phân loại và điều hướng các câu lệnh SQL.

Tích hợp với DB Sandbox (`data/security_lab/sandbox_db.py`):
  - Khi `security_lab=True` (chế độ Security Lab): Phân loại câu lệnh (`classify_sql`) và cho phép truyền câu lệnh sang Sandbox DB để thực thi an toàn với cơ chế Auto-Rollback.
  - Khi `security_lab=False` (chế độ Strict Production): Kiểm tra từ khóa bị cấm và raise `SQLInjectionError`.
"""

import re
import logging
from app.core.config import get_settings
from app.core.exceptions import SQLInjectionError
from data.security_lab.sandbox_db import classify_sql, SQLCategory

logger = logging.getLogger(__name__)

FORBIDDEN_KEYWORDS: list[str] = [
    "INSERT", "UPDATE", "DELETE", "MERGE", "UPSERT", "REPLACE",
    "DROP", "CREATE", "ALTER", "TRUNCATE", "RENAME",
    "GRANT", "REVOKE",
    "COMMIT", "ROLLBACK", "SAVEPOINT",
    "EXEC", "EXECUTE", "CALL", "COPY", "VACUUM", "ANALYZE"
]

_FORBIDDEN_PATTERN: re.Pattern = re.compile(
    r"\b(" + "|".join(re.escape(kw) for kw in FORBIDDEN_KEYWORDS) + r")\b",
    flags=re.IGNORECASE,
)


def validate_sql(sql: str) -> str:
    """
    Kiểm tra và phân loại câu lệnh SQL do LLM sinh ra.

    Args:
        sql: Câu lệnh SQL cần kiểm tra.

    Returns:
        sql đã chuẩn hóa (strip).

    Raises:
        SQLInjectionError: Nếu security_lab=False và phát hiện câu lệnh nguy hiểm.
    """
    cleaned = sql.strip()
    if not cleaned:
        return cleaned

    category = classify_sql(cleaned)
    settings = get_settings()

    logger.info(f"[SQLValidator] Phân loại câu lệnh: [{category.value}] | SecurityLab: {settings.security_lab}")

    # Trong chế độ Security Lab, không chặn regex tĩnh mà đẩy trách nhiệm cách ly cho Sandbox DB
    if settings.security_lab:
        logger.debug(f"[SQLValidator] Chấp nhận câu lệnh [{category.value}] cho Sandbox DB execution.")
        return cleaned

    # Chế độ Strict: Chặn từ khóa nguy hiểm ngoại trừ SELECT/READ
    match = _FORBIDDEN_PATTERN.search(cleaned)
    if match:
        forbidden_kw = match.group(0).upper()
        logger.warning(
            f"[SQLValidator] Strictly rejected dangerous query keyword '{forbidden_kw}' in non-lab mode. SQL: {cleaned[:200]}"
        )
        raise SQLInjectionError(forbidden_keyword=forbidden_kw)

    return cleaned


def is_safe_sql(sql: str) -> bool:
    """
    Phiên bản boolean của validate_sql.

    Returns:
        True nếu an toàn/chấp nhận, False nếu bị từ chối.
    """
    try:
        validate_sql(sql)
        return True
    except SQLInjectionError:
        return False
