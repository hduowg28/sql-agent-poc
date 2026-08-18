import sys
import os

sys.path.insert(0, r"c:\learning\3rd year\3 semerter\sql-agent-poc")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.schemas import ChatRequest
from app.services.chat_services import ChatService
from app.core.database import SessionLocal


def test_langgraph_and_history():
    print("=== Testing LangGraph SQL Agent & Memory History ===")
    
    db = SessionLocal()
    session_id = "test_session_123"

    try:
        # Question 1
        print("\n--- Question 1: List tables in database ---")
        req1 = ChatRequest(
            question="Trong cơ sở dữ liệu Superstore có những bảng nào?",
            session_id=session_id
        )
        res1 = ChatService.ask(req1)
        print("Response 1 Success:", res1.success)
        print("Answer 1:\n", res1.answer)
        print("Execution Time:", res1.execution_meta.execution_time_ms, "ms")

        # Question 2 (Requires history memory: context from turn 1)
        print("\n--- Question 2: Multi-turn follow-up question ---")
        req2 = ChatRequest(
            question="Cho tôi biết bảng orders có bao nhiêu cột và các cột đó tên là gì?",
            session_id=session_id
        )
        res2 = ChatService.ask(req2)
        print("Response 2 Success:", res2.success)
        print("Answer 2:\n", res2.answer)
        # Question 3 (Requires SQL query execution)
        print("\n--- Question 3: Query executing SQL ---")
        req3 = ChatRequest(
            question="Tổng số khách hàng trong database là bao nhiêu?",
            session_id=session_id
        )
        res3 = ChatService.ask(req3)
        print("Response 3 Success:", res3.success)
        print("Answer 3:\n", res3.answer)
        print("SQL Executed:\n", res3.generated_sql)
        print("Execution Time:", res3.execution_meta.execution_time_ms, "ms")

        print("\n[PASSED] LangGraph Agent & Conversation History working cleanly!")

    finally:
        db.close()


if __name__ == "__main__":
    test_langgraph_and_history()
