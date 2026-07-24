"""
app/services/chat_services.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Business Logic layer cho Chat endpoint.

Thay đổi so với phiên bản cũ:
  - Nhận `Session` qua Dependency Injection thay vì import global
  - Không import `agent` trực tiếp → dùng `get_agent()` singleton
  - Thay HTTPException bằng Custom Exceptions (xử lý bởi Global Handler)
  - Đo thời gian thực thi và trả về `ChatExecutionMeta`
  - `ask()` nhận thêm `db: Session` để sẵn sàng cho các query trực tiếp sau này
"""

import logging
import time

from sqlalchemy.orm import Session

from app.agents.sql_agent import get_agent
from app.core.exceptions import AgentException, ValidationException
from app.schemas.chat import ChatExecutionMeta, ChatRequest, ChatResponse

logger = logging.getLogger(__name__)


class ChatService:

    # -----------------------------------------------------------------------
    # Validation
    # -----------------------------------------------------------------------
    @staticmethod
    def validate_question(question: str) -> str:
        """
        Kiểm tra câu hỏi hợp lệ trước khi gửi cho Agent.
        Raise ValidationException thay vì HTTPException để Global Handler xử lý.
        """
        question = question.strip()

        if not question:
            raise ValidationException(
                field="question",
                detail="Câu hỏi không được để trống.",
            )

        if len(question) > 2000:
            raise ValidationException(
                field="question",
                detail=f"Câu hỏi quá dài (tối đa 2000 ký tự, hiện tại {len(question)}).",
            )

        return question

    # -----------------------------------------------------------------------
    # Agent Runner
    # -----------------------------------------------------------------------
    @staticmethod
    def run_agent(question: str) -> tuple[dict, float]:
        """
        Gửi câu hỏi đến SQL Agent và đo thời gian thực thi.

        Returns:
            (result_dict, elapsed_ms)

        Raises:
            AgentException: khi Agent gặp lỗi không mong muốn.
        """
        agent = get_agent()
        start = time.perf_counter()

        try:
            result = agent.invoke({"input": question})
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.info(
                f"[ChatService] Agent hoàn tất | "
                f"question_len={len(question)} | elapsed={elapsed_ms:.1f}ms"
            )
            return result, elapsed_ms

        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.error(f"[ChatService] Agent lỗi sau {elapsed_ms:.1f}ms: {exc}")
            raise AgentException(
                message="Agent không thể xử lý câu hỏi.",
                detail=str(exc),
            ) from exc

    # -----------------------------------------------------------------------
    # Response Formatter
    # -----------------------------------------------------------------------
    @staticmethod
    def format_response(result: dict, elapsed_ms: float) -> ChatResponse:
        """Chuyển output của Agent thành ChatResponse schema chuẩn."""
        answer = result.get("output", "Không có kết quả.")

        # Cố gắng trích xuất SQL từ intermediate_steps nếu có
        generated_sql: str | None = None
        intermediate = result.get("intermediate_steps", [])
        for action, _ in intermediate:
            tool_input = getattr(action, "tool_input", None)
            if tool_input and isinstance(tool_input, str) and tool_input.strip().upper().startswith("SELECT"):
                generated_sql = tool_input.strip()
                break

        meta = ChatExecutionMeta(
            execution_time_ms=round(elapsed_ms, 2),
            sql_executed=generated_sql is not None,
        )

        return ChatResponse(
            success=True,
            answer=answer,
            generated_sql=generated_sql,
            execution_meta=meta,
        )

    # -----------------------------------------------------------------------
    # Public Entry Point
    # -----------------------------------------------------------------------
    @classmethod
    def ask(cls, request: ChatRequest, db: Session) -> ChatResponse:
        """
        Pipeline hoàn chỉnh: validate → run → format.

        Args:
            request: ChatRequest schema từ API layer.
            db: SQLAlchemy Session (Dependency Injected).

        Returns:
            ChatResponse đã được định dạng.
        """
        question = cls.validate_question(request.question)
        result, elapsed_ms = cls.run_agent(question)
        return cls.format_response(result, elapsed_ms)