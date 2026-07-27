"""
app/handlers/error_handler.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Global Exception Handlers cho FastAPI.

Đăng ký vào app qua `register_exception_handlers(app)` trong main.py.
Mỗi handler chuyển Custom Exception → JSON response chuẩn với HTTP status code phù hợp.
"""

import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.core.exceptions import (
    AppException,
    DatabaseException,
    DatabaseConnectionError,
    SQLInjectionError,
    AgentTimeoutError,
    AgentException,
    ValidationException,
)

logger = logging.getLogger(__name__)


def _error_response(
    status_code: int,
    error_type: str,
    message: str,
    detail: str | None = None,
) -> JSONResponse:
    body = {
        "success": False,
        "error": {
            "type": error_type,
            "message": message,
        },
    }
    if detail:
        body["error"]["detail"] = detail
    return JSONResponse(status_code=status_code, content=body)

async def handle_sql_injection_error(request: Request, exc: SQLInjectionError) -> JSONResponse:
    logger.warning(
        f"[SecurityGuard] SQLInjectionError | path={request.url.path} "
        f"| keyword={exc.forbidden_keyword}"
    )
    return _error_response(
        status_code=status.HTTP_403_FORBIDDEN,
        error_type="SQLInjectionError",
        message=exc.message,
        detail=exc.detail,
    )


async def handle_agent_timeout(request: Request, exc: AgentTimeoutError) -> JSONResponse:
    logger.error(f"[Agent] Timeout | path={request.url.path} | detail={exc.detail}")
    return _error_response(
        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        error_type="AgentTimeoutError",
        message=exc.message,
        detail=exc.detail,
    )


async def handle_agent_exception(request: Request, exc: AgentException) -> JSONResponse:
    logger.error(f"[Agent] AgentException | path={request.url.path} | {exc}")
    return _error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_type="AgentException",
        message=exc.message,
        detail=exc.detail,
    )


async def handle_db_connection_error(request: Request, exc: DatabaseConnectionError) -> JSONResponse:
    logger.critical(f"[DB] ConnectionError | path={request.url.path} | {exc}")
    return _error_response(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        error_type="DatabaseConnectionError",
        message=exc.message,
        detail=exc.detail,
    )


async def handle_database_exception(request: Request, exc: DatabaseException) -> JSONResponse:
    logger.error(f"[DB] DatabaseException | path={request.url.path} | {exc}")
    return _error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_type="DatabaseException",
        message=exc.message,
        detail=exc.detail,
    )


async def handle_validation_exception(request: Request, exc: ValidationException) -> JSONResponse:
    logger.warning(f"[Validation] ValidationException | path={request.url.path} | {exc}")
    return _error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error_type="ValidationException",
        message=exc.message,
        detail=exc.detail,
    )


async def handle_app_exception(request: Request, exc: AppException) -> JSONResponse:
    """Fallback handler cho mọi AppException chưa được handle cụ thể."""
    logger.error(f"[App] Unhandled AppException | path={request.url.path} | {exc}")
    return _error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_type="AppException",
        message=exc.message,
        detail=exc.detail,
    )


async def handle_sqlalchemy_error(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    logger.error(f"[SQLAlchemy] SQLAlchemyError | path={request.url.path} | {exc}")
    return _error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_type="DatabaseError",
        message="Lỗi database không xác định.",
        detail=str(exc.__class__.__name__),
    )


async def handle_request_validation_error(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle lỗi Pydantic validation từ FastAPI request body."""
    errors = exc.errors()
    logger.warning(f"[FastAPI] RequestValidationError | path={request.url.path} | {errors}")
    return _error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error_type="RequestValidationError",
        message="Dữ liệu request không hợp lệ.",
        detail=str(errors),
    )


async def handle_unhandled_exception(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all: không để lộ stack trace ra ngoài."""
    logger.exception(f"[App] Unhandled Exception | path={request.url.path} | {exc}")
    return _error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_type="InternalServerError",
        message="Đã xảy ra lỗi hệ thống. Vui lòng thử lại sau.",
    )

def register_exception_handlers(app: FastAPI) -> None:
    """
    Đăng ký toàn bộ exception handlers vào FastAPI app.
    Thứ tự quan trọng: handler cụ thể phải đứng TRƯỚC handler tổng quát.

    Gọi trong main.py:
        from app.handlers.error_handler import register_exception_handlers
        register_exception_handlers(app)
    """
    # Specific custom exceptions (theo thứ tự từ cụ thể → tổng quát)
    app.add_exception_handler(SQLInjectionError, handle_sql_injection_error)
    app.add_exception_handler(AgentTimeoutError, handle_agent_timeout)
    app.add_exception_handler(AgentException, handle_agent_exception)
    app.add_exception_handler(DatabaseConnectionError, handle_db_connection_error)
    app.add_exception_handler(DatabaseException, handle_database_exception)
    app.add_exception_handler(ValidationException, handle_validation_exception)
    app.add_exception_handler(AppException, handle_app_exception)

    # SQLAlchemy errors
    app.add_exception_handler(SQLAlchemyError, handle_sqlalchemy_error)

    # FastAPI built-in validation
    app.add_exception_handler(RequestValidationError, handle_request_validation_error)

    # Final catch-all
    app.add_exception_handler(Exception, handle_unhandled_exception)

    logger.info("[App] Exception handlers đã được đăng ký.")
