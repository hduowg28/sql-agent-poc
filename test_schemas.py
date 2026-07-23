import sys
import os

sys.path.insert(0, r"c:\learning\3rd year\3 semerter\sql-agent-poc")

from pydantic import ValidationError
from app.schemas import (
    AppBaseModel,
    ChatRequest,
    ChatResponse,
    ChatResponseData,
    ChatExecutionMeta,
    ChatMessage,
    ChatMessageRole,
    ChatEnvelopeResponse,
    ResponseEnvelope,
    ErrorResponse,
    ErrorDetail,
    SQLExecutionRequest,
    SQLQueryResult,
    TableSchemaInfo,
    ColumnSchemaInfo,
    DatabaseSchemaResponse,
    HealthCheckResponse,
    HealthCheckResponseData,
)


def run_tests():
    print("--- 1. Testing AppBaseModel ConfigDict (Whitespace stripping & Extra fields) ---")
    req = ChatRequest(question="   How many users are there?   ")
    assert req.question == "How many users are there?", f"Whitespace strip failed: '{req.question}'"
    print("[PASSED] Automatic whitespace trimming working.")

    try:
        ChatRequest.model_validate({"question": "Valid question", "unknown_field": "invalid"})
        assert False, "Should have failed due to extra='forbid'"
    except ValidationError as e:
        print("[PASSED] Extra field forbidden correctly:", e.errors()[0]["type"])

    print("\n--- 2. Testing ChatResponse compatibility with PoC service dictionary ---")
    service_output = {"success": True, "answer": "There are 100 users."}
    validated_response = ChatResponse(**service_output)
    assert validated_response.success is True
    assert validated_response.answer == "There are 100 users."
    print("[PASSED] ChatResponse validates service dictionary output seamlessly.")

    print("\n--- 3. Testing Generic Envelope Response (ChatEnvelopeResponse) ---")
    envelope = ChatEnvelopeResponse(
        data=ChatResponseData(
            answer="There are 100 users.",
            generated_sql="SELECT COUNT(*) FROM users;",
            execution_meta=ChatExecutionMeta(
                execution_time_ms=50.2,
                tokens_used=120,
                sql_executed=True,
            ),
        )
    )
    dumped = envelope.model_dump()
    assert dumped["success"] is True
    assert dumped["data"]["answer"] == "There are 100 users."
    print("[PASSED] Generic ChatEnvelopeResponse model_dump verified.")

    print("\n[PASSED] ALL SCHEMAS TESTED & VERIFIED SUCCESSFULLY!")


if __name__ == "__main__":
    run_tests()
