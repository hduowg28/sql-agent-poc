"""
tests/test_customer_api.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Test suite kiểm thử toàn bộ Customer Business API & Custom LLM Tools.
"""

import sys
import os
import uuid

sys.path.insert(0, os.getcwd())

from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal, engine
from langchain_community.utilities import SQLDatabase
from app.agents.tools import (
    GetCustomerTool,
    RegisterCustomerTool,
    ListTablesTool,
    GetTableSchemaTool,
    SafeSQLQueryTool,
)

client = TestClient(app)


def test_get_customer_success():
    """GET /api/customers/{customer_id} với customer có sẵn -> 200 OK."""
    response = client.get("/api/customers/CG-12520")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert data["customer_id"] == "CG-12520"
    assert "customer_name" in data
    assert "segment" in data


def test_get_customer_not_found():
    """GET /api/customers/{customer_id} không tồn tại -> 404 Not Found."""
    response = client.get("/api/customers/NON-EXISTENT-CUST-999")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["error"]["type"] == "CustomerNotFoundException"


def test_post_customer_success():
    """POST /api/customers đăng ký thành công -> 201 Created."""
    unique_name = f"Test User {uuid.uuid4().hex[:6]}"
    payload = {
        "customer_name": unique_name,
        "segment": "Consumer",
        "country": "United States",
        "city": "San Francisco",
        "state": "California",
        "postal_code": "94101",
        "region": "West",
    }
    response = client.post("/api/customers", json=payload)
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    data = response.json()
    assert data["customer_name"] == unique_name
    assert data["customer_id"].startswith("CUST-")


def test_post_customer_missing_required_field():
    """POST /api/customers thiếu customer_name -> 422 Unprocessable Entity."""
    payload = {
        "segment": "Consumer",
        "city": "San Francisco",
    }
    response = client.post("/api/customers", json=payload)
    assert response.status_code == 422


def test_post_customer_extra_field_forbidden():
    """POST /api/customers gửi extra field không cho phép -> 422 Unprocessable Entity (extra='forbid')."""
    payload = {
        "customer_name": "Forbidden Extra User",
        "customer_id": "CLIENT-INJECTED-ID",  # Client cố tình override customer_id
    }
    response = client.post("/api/customers", json=payload)
    assert response.status_code == 422


def test_get_customer_tool():
    """Kiểm tra GetCustomerTool gọi đúng CustomerService."""
    db = SQLDatabase(engine)
    tool = GetCustomerTool(db=db)
    result = tool._run("CG-12520")
    assert "CG-12520" in result
    assert "customer_name" in result


def test_register_customer_tool():
    """Kiểm tra RegisterCustomerTool gọi đúng CustomerService."""
    unique_name = f"Tool User {uuid.uuid4().hex[:6]}"
    db = SQLDatabase(engine)
    tool = RegisterCustomerTool(db=db)
    tool_input = f"customer_name: {unique_name}, segment: Corporate, city: Chicago"
    result = tool._run(tool_input)
    assert "Đăng ký khách hàng thành công" in result
    assert unique_name in result


def test_existing_sql_tools_integrity():
    """Đảm bảo các tools cũ vẫn hoạt động bình thường."""
    db = SQLDatabase(engine)
    list_tool = ListTablesTool(db=db)
    schema_tool = GetTableSchemaTool(db=db)
    query_tool = SafeSQLQueryTool(db=db)

    assert "customers" in list_tool._run()
    assert "customers" in schema_tool._run("customers")
    res = query_tool._run("SELECT count(*) FROM customers;")
    assert "[READ]" in res and "[(" in res


def main():
    print("=== 1. Testing GET /api/customers/{customer_id} (Existing) ===")
    test_get_customer_success()
    print("[PASSED] GET existing customer -> 200 OK")

    print("\n=== 2. Testing GET /api/customers/{customer_id} (Non-existing) ===")
    test_get_customer_not_found()
    print("[PASSED] GET non-existing customer -> 404 Not Found")

    print("\n=== 3. Testing POST /api/customers (Valid Register) ===")
    test_post_customer_success()
    print("[PASSED] POST valid customer -> 201 Created")

    print("\n=== 4. Testing POST /api/customers (Missing Field) ===")
    test_post_customer_missing_required_field()
    print("[PASSED] POST missing field -> 422 Unprocessable Entity")

    print("\n=== 5. Testing POST /api/customers (Extra Forbidden Field) ===")
    test_post_customer_extra_field_forbidden()
    print("[PASSED] POST extra field forbidden -> 422 Unprocessable Entity")

    print("\n=== 6. Testing GetCustomerTool ===")
    test_get_customer_tool()
    print("[PASSED] GetCustomerTool executed CustomerService correctly.")

    print("\n=== 7. Testing RegisterCustomerTool ===")
    test_register_customer_tool()
    print("[PASSED] RegisterCustomerTool executed CustomerService correctly.")

    print("\n=== 8. Testing Existing SQL Tools Integrity ===")
    test_existing_sql_tools_integrity()
    print("[PASSED] Existing SQL tools (ListTables, GetSchema, SafeSQLQuery) working cleanly.")

    print("\n[ALL TESTS PASSED SUCCESSFULLY!]")


if __name__ == "__main__":
    main()
