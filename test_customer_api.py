import sys
import os

sys.path.insert(0, r"c:\learning\3rd year\3 semerter\sql-agent-poc")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient
from app.main import app

import uuid

client = TestClient(app)


def test_customer_apis():
    print("=== Testing Customer Business APIs (get_customer & register_customer) ===")

    test_id = f"TEST-CUST-{uuid.uuid4().hex[:6].upper()}"
    
    # 1. Register customer with explicit customer_id
    print("\n--- 1. Testing register_customer (explicit ID) ---")
    payload = {
        "customer_id": test_id,
        "customer_name": "Tran Van Test",
        "segment": "Corporate",
        "country": "Vietnam",
        "city": "Da Nang",
        "state": "Da Nang",
        "postal_code": "550000",
        "region": "Central"
    }
    resp = client.post("/api/v1/customers/register", json=payload)
    print("Status Code:", resp.status_code)
    data = resp.json()
    print("Response Body:", data)
    assert resp.status_code == 201, f"Expected 201, got {resp.status_code}"
    assert data["success"] is True
    assert data["data"]["customer_id"] == test_id
    assert data["data"]["customer_name"] == "Tran Van Test"
    print("[PASSED] Customer registered successfully with explicit ID.")

    # 2. Get registered customer details
    print("\n--- 2. Testing get_customer (existing ID) ---")
    resp = client.get(f"/api/v1/customers/{test_id}")
    print("Status Code:", resp.status_code)
    data = resp.json()
    print("Response Body:", data)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    assert data["success"] is True
    assert data["data"]["customer_id"] == test_id
    assert data["data"]["city"] == "Da Nang"
    print("[PASSED] Retrieved customer details successfully.")

    # 3. Register duplicate customer_id (Should fail with 409 Conflict)
    print("\n--- 3. Testing register_customer (duplicate ID -> 409) ---")
    resp = client.post("/api/v1/customers/register", json=payload)
    print("Status Code:", resp.status_code)
    data = resp.json()
    print("Response Body:", data)
    assert resp.status_code == 409, f"Expected 409, got {resp.status_code}"
    assert data["success"] is False
    assert data["error"]["type"] == "CustomerAlreadyExistsException"
    print("[PASSED] Duplicate registration rejected with 409 Conflict.")

    # 4. Get non-existent customer (Should fail with 404 Not Found)
    print("\n--- 4. Testing get_customer (non-existent ID -> 404) ---")
    resp = client.get("/api/v1/customers/NON-EXISTENT-ID-XYZ")
    print("Status Code:", resp.status_code)
    data = resp.json()
    print("Response Body:", data)
    assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"
    assert data["success"] is False
    assert data["error"]["type"] == "CustomerNotFoundException"
    print("[PASSED] Non-existent customer request handled with 404 Not Found.")

    # 5. Register customer with auto-generated ID (no customer_id provided)
    print("\n--- 5. Testing register_customer (auto-generated ID) ---")
    payload_auto = {
        "customer_name": "Le Thi Auto",
        "segment": "Consumer",
        "country": "Vietnam"
    }
    resp = client.post("/api/v1/customers/register", json=payload_auto)
    print("Status Code:", resp.status_code)
    data = resp.json()
    print("Response Body:", data)
    assert resp.status_code == 201, f"Expected 201, got {resp.status_code}"
    assert data["success"] is True
    assert data["data"]["customer_id"].startswith("CUST-")
    assert data["data"]["customer_name"] == "Le Thi Auto"
    print("[PASSED] Customer registered with auto-generated ID.")

    # 6. Register customer with empty name (Should fail with 422 Validation Error)
    print("\n--- 6. Testing register_customer (empty name -> 422) ---")
    payload_invalid = {
        "customer_name": "   "
    }
    resp = client.post("/api/v1/customers/register", json=payload_invalid)
    print("Status Code:", resp.status_code)
    data = resp.json()
    print("Response Body:", data)
    assert resp.status_code == 422, f"Expected 422, got {resp.status_code}"
    assert data["success"] is False
    print("[PASSED] Validation error triggered for empty name.")

    print("\n=======================================================")
    print("[ALL TESTS PASSED] Customer business APIs fully verified!")
    print("=======================================================")


if __name__ == "__main__":
    test_customer_apis()
