import sys
import os
import uuid

sys.path.insert(0, r"c:\learning\3rd year\3 semerter\sql-agent-poc")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.agents.tools import GetCustomerTool, RegisterCustomerTool


def test_agent_tools_directly():
    print("=== Testing Agent Custom Tools (GetCustomerTool & RegisterCustomerTool) ===")

    test_id = f"AI-CUST-{uuid.uuid4().hex[:6].upper()}"

    # 1. Test RegisterCustomerTool
    print("\n--- 1. Testing RegisterCustomerTool ---")
    reg_tool = RegisterCustomerTool()
    reg_result = reg_tool.run({
        "customer_id": test_id,
        "customer_name": "AI Test Customer",
        "segment": "Consumer",
        "country": "Vietnam",
        "city": "Hanoi"
    })
    print("Register Tool Result:\n", reg_result)
    assert "Đăng ký khách hàng thành công" in reg_result
    assert test_id in reg_result
    print("[PASSED] RegisterCustomerTool executed successfully.")

    # 2. Test GetCustomerTool
    print("\n--- 2. Testing GetCustomerTool ---")
    get_tool = GetCustomerTool()
    get_result = get_tool.run({"customer_id": test_id})
    print("Get Customer Tool Result:\n", get_result)
    assert test_id in get_result
    assert "AI Test Customer" in get_result
    assert "Hanoi" in get_result
    print("[PASSED] GetCustomerTool executed successfully.")

    print("\n=======================================================")
    print("[ALL TESTS PASSED] AI Agent Customer Tools fully working!")
    print("=======================================================")


if __name__ == "__main__":
    test_agent_tools_directly()
