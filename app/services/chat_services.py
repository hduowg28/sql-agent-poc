"""
app/services/chat_services.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Business Logic layer cho Chat endpoint.

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
        raw_output = result.get("output", "Không có kết quả.")

        # Xử lý đa dạng kiểu dữ liệu của raw_output (str, list[dict], dict)
        if isinstance(raw_output, str):
            answer = raw_output.strip()
        elif isinstance(raw_output, list):
            extracted_texts = []
            for item in raw_output:
                if isinstance(item, dict) and "text" in item:
                    extracted_texts.append(str(item["text"]))
                elif isinstance(item, str):
                    extracted_texts.append(item)
                else:
                    extracted_texts.append(str(item))
            answer = "\n".join(extracted_texts).strip() if extracted_texts else "Không có kết quả."
        elif isinstance(raw_output, dict) and "text" in raw_output:
            answer = str(raw_output["text"]).strip()
        else:
            answer = str(raw_output).strip()

        # Trích xuất SQL từ intermediate_steps nếu có
        generated_sql: str | None = None
        intermediate = result.get("intermediate_steps", [])
        for action, _ in intermediate:
            tool_input = getattr(action, "tool_input", None)
            sql_candidate: str | None = None

            if isinstance(tool_input, str):
                sql_candidate = tool_input
            elif isinstance(tool_input, dict):
                sql_candidate = tool_input.get("query") or tool_input.get("sql") or tool_input.get("sql_query")

            if sql_candidate and isinstance(sql_candidate, str):
                cleaned_candidate = sql_candidate.strip()
                if cleaned_candidate.upper().startswith("SELECT"):
                    generated_sql = cleaned_candidate
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