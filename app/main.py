"""
app/main.py
~~~~~~~~~~~
FastAPI application entry point.

  - Dùng `lifespan` context manager thay `@app.on_event` (deprecated)
  - Đăng ký Global Exception Handlers qua `register_exception_handlers()`
  - Kiểm tra DB connection khi startup (fail-fast)
  - Pre-warm SQL Agent singleton khi startup
  - Thêm CORS, metadata cho OpenAPI docs
"""

import logging
import warnings
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import verify_db_connection
from app.handlers.error_handler import register_exception_handlers

warnings.filterwarnings("ignore", category=DeprecationWarning, module="langchain_community")

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Chạy khi app khởi động và khi tắt.
    - startup  : kiểm tra DB, pre-warm Agent
    - shutdown : log thông báo dọn dẹp
    """
    logger.info("=" * 55)
    logger.info(f"  SQL Agent POC  |  env={settings.app_env}")
    logger.info("=" * 55)

    # 1. Kiểm tra kết nối DB (fail-fast)
    verify_db_connection()

    # 2. Pre-warm Agent singleton (tránh cold-start ở request đầu)
    logger.info("[Startup] Pre-warming SQL Agent...")
    from app.agents.sql_agent import get_agent
    get_agent()
    logger.info("[Startup] Sẵn sàng nhận request.")

    yield  # ← App đang chạy

    # --- Shutdown ---
    logger.info("[Shutdown] Đang tắt ứng dụng...")

def create_app() -> FastAPI:
    """Tạo FastAPI instance với đầy đủ cấu hình."""
    application = FastAPI(
        title="SQL Agent POC",
        description=(
            "Hệ thống hỏi đáp dữ liệu bằng ngôn ngữ tự nhiên, "
            "sử dụng LangChain SQL Agent + Google Gemini."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS (cho phép gọi từ frontend local khi dev)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.app_env == "development" else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global Exception Handlers
    register_exception_handlers(application)

    # Routers
    from app.api.chat import router as chat_router
    application.include_router(chat_router, prefix="/api/v1")

    # Health check endpoint
    @application.get("/health", tags=["System"])
    def health_check() -> dict:
        """Kiểm tra trạng thái hoạt động của server."""
        return {"status": "ok", "env": settings.app_env}

    return application

app = create_app()
