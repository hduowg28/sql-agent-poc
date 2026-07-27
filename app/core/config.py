from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    database_url: str

    db_pool_size: int = 5          
    db_max_overflow: int = 10      
    db_pool_timeout: int = 30      
    db_pool_recycle: int = 1800    
    db_pool_pre_ping: bool = True

    gemini_api_key: str = ""

    app_env: str = "development"
    debug: bool = False


def get_settings() -> Settings:
    """
    Trả về Settings instance từ file .env / environment variables.
    """
    return Settings()

settings = get_settings()

