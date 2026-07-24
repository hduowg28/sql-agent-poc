from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # --- Database ---
    database_url: str

    # Connection Pool Parameters
    db_pool_size: int = 5          # Số connection thường trực trong pool
    db_max_overflow: int = 10      # Số connection tạm thời thêm khi pool đầy
    db_pool_timeout: int = 30      # Giây chờ lấy connection từ pool
    db_pool_recycle: int = 1800    # Giây trước khi connection bị tái tạo (tránh stale)
    db_pool_pre_ping: bool = True  # Kiểm tra connection còn sống trước khi dùng

    # --- Gemini / LLM ---
    gemini_api_key: str = ""

    # --- Application ---
    app_env: str = "development"
    debug: bool = False


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Trả về Settings singleton (cache lần đầu, dùng lại sau).
    Dùng lru_cache để tránh đọc file .env nhiều lần.
    """
    return Settings()


# Singleton instance dùng trong toàn ứng dụng
settings = get_settings()
