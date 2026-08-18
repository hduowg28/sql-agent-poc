"""
app/services/chat_services.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Business Logic layer cho Chat endpoint với LangGraph & Conversation History support.

  - Nhận `Session` qua Dependency Injection
  - Sử dụng `get_agent()` singleton trả về LangGraph CompiledStateGraph
  - Quản lý bộ nhớ hội thoại tự động qua `session_id` (LangGraph thread_id)
  - Đo thời gian thực thi và trả về `ChatExecutionMeta`
"""

import logging
import time

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from app.agents.sql_agent import get_agent
from app.core.exceptions import AgentException, ValidationException
from app.schemas.chat import (
    ChatExecutionMeta,
    ChatMessage,
    ChatMessageRole,
    ChatRequest,
    ChatResponse,
)

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
    def run_agent(
        question: str,
        session_id: str | None = None,
        history: list[ChatMessage] | None = None,
    ) -> tuple[dict, float]:
        """
        Gửi câu hỏi đến LangGraph SQL Agent và đo thời gian thực thi.
        Hỗ trợ conversation history qua `session_id` (thread_id).

        Returns:
            (result_dict, elapsed_ms)
        """
        agent = get_agent()
        start = time.perf_counter()

        # Chuẩn bị tin nhắn truyền vào LangGraph
        input_messages: list[BaseMessage] = []
        if history:
            for msg in history:
                if msg.role == ChatMessageRole.USER:
                    input_messages.append(HumanMessage(content=msg.content))
                elif msg.role == ChatMessageRole.ASSISTANT:
                    input_messages.append(AIMessage(content=msg.content))

        input_messages.append(HumanMessage(content=question))

        # Cấu hình thread_id cho MemorySaver checkpointer của LangGraph
        thread_id = session_id if session_id else "default_session"
        config = {"configurable": {"thread_id": thread_id}}

        try:
            result = agent.invoke({"messages": input_messages}, config=config)
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.info(
                f"[ChatService] LangGraph Agent hoàn tất | "
                f"session_id={thread_id} | question_len={len(question)} | elapsed={elapsed_ms:.1f}ms"
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
    def format_response(
        result: dict,
        elapsed_ms: float,
        include_sql: bool = True,
    ) -> ChatResponse:
        """Chuyển output của LangGraph Agent thành ChatResponse schema chuẩn."""
        messages: list[BaseMessage] = result.get("messages", [])

        answer = "Không có kết quả."
        generated_sql: str | None = None

        # Trích xuất câu trả lời cuối cùng từ AIMessage có nội dung
        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and msg.content:
                extracted = ""
                if isinstance(msg.content, str) and msg.content.strip():
                    extracted = msg.content.strip()
                elif isinstance(msg.content, list):
                    text_parts = []
                    for item in msg.content:
                        if isinstance(item, str) and item.strip():
                            text_parts.append(item.strip())
                        elif isinstance(item, dict) and "text" in item and str(item["text"]).strip():
                            text_parts.append(str(item["text"]).strip())
                    if text_parts:
                        extracted = "\n".join(text_parts).strip()

                if extracted:
                    answer = extracted
                    break

        # Trích xuất SQL query từ tool_calls trong danh sách messages
        executed_sqls: list[str] = []
        for msg in messages:
            tool_calls = []
            if isinstance(msg, AIMessage):
                if getattr(msg, "tool_calls", None):
                    tool_calls.extend(msg.tool_calls)
                if hasattr(msg, "additional_kwargs") and msg.additional_kwargs.get("tool_calls"):
                    tool_calls.extend(msg.additional_kwargs["tool_calls"])

            for tc in tool_calls:
                tool_name = tc.get("name") if isinstance(tc, dict) else getattr(tc, "name", None)
                if tool_name in ("sql_query", "safe_sql_query", "vulnerable_sql_tool", "execute_raw_sql"):
                    args = tc.get("args") if isinstance(tc, dict) else getattr(tc, "args", {})
                    if isinstance(args, str):
                        try:
                            import json
                            args = json.loads(args)
                        except Exception:
                            args = {"query": args}
                    if isinstance(args, dict):
                        sql_cand = args.get("query") or args.get("sql")
                        if sql_cand and isinstance(sql_cand, str) and sql_cand.strip():
                            executed_sqls.append(sql_cand.strip())

        if executed_sqls and include_sql:
            generated_sql = "\n\n".join(executed_sqls)

        meta = ChatExecutionMeta(
            execution_time_ms=round(elapsed_ms, 2),
            sql_executed=bool(executed_sqls),
        )

        return ChatResponse(
            success=True,
            answer=answer,
            generated_sql=generated_sql if include_sql else None,
            execution_meta=meta,
        )

    # -----------------------------------------------------------------------
    # Public Entry Point
    # -----------------------------------------------------------------------
    @classmethod
    def ask(cls, request: ChatRequest) -> ChatResponse:
        """
        Pipeline hoàn chỉnh: validate → run → format.
        Args:
            request: ChatRequest schema từ API layer.

        Returns:
            ChatResponse đã được định dạng.
        """
        question = cls.validate_question(request.question)
        result, elapsed_ms = cls.run_agent(
            question=question,
            session_id=request.session_id,
            history=request.history,
        )
        return cls.format_response(
            result=result,
            elapsed_ms=elapsed_ms,
            include_sql=request.include_sql,
        )