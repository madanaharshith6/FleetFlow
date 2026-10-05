"""
Targeted Rule 22 Edge Case & Error Handling Verification
"""
import urllib.request
import urllib.parse
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

def request(method, path, data=None, token=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            resp_body = resp.read().decode("utf-8")
            return resp.status, json.loads(resp_body) if resp_body else {}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            err_json = json.loads(err_body)
        except Exception:
            err_json = {"detail": err_body}
        return e.code, err_json

def test_edge_cases():
    print("Testing Rule 22 Error Handling & Edge Cases...")

    # 1. Login as Admin
    status, auth_data = request("POST", "/api/auth/login", {"email": "admin@fleetflow.com", "password": "Admin@123"})
    assert status == 200, f"Login failed: {auth_data}"
    token = auth_data.get("token") or auth_data.get("access_token")
    print("[PASS] Authenticated as Admin")

    # 2. Missing vehicle in maintenance creation
    status, res = request("POST", "/api/maintenance", {
        "vehicle_id": 999999,
        "category": "Oil Change",
        "description": "Test missing vehicle",
        "scheduled_date": "2026-10-10T10:00:00"
    }, token=token)
    assert status == 404, f"Expected 404 for missing vehicle, got {status}: {res}"
    print(f"[PASS] Missing vehicle returns 404: {res.get('detail')}")

    # 3. Invalid maintenance category
    status, res = request("POST", "/api/maintenance", {
        "vehicle_id": 1,
        "category": "Flying Carpet Service",
        "description": "Test invalid category",
        "scheduled_date": "2026-10-10T10:00:00"
    }, token=token)
    assert status == 400, f"Expected 400 for invalid category, got {status}: {res}"
    print(f"[PASS] Invalid category returns 400: {res.get('detail')}")

    # 4. Invalid maintenance ID
    status, res = request("GET", "/api/maintenance/MNT-NONEXISTENT", token=token)
    assert status == 404, f"Expected 404 for invalid maintenance ID, got {status}: {res}"
    print(f"[PASS] Invalid maintenance ID returns 404: {res.get('detail')}")

    # 5. Invalid status update
    status, res = request("PUT", "/api/maintenance/1/status", {"status": "SuperDuper"}, token=token)
    assert status == 400, f"Expected 400 for invalid status, got {status}: {res}"
    print(f"[PASS] Invalid maintenance status returns 400: {res.get('detail')}")

    # 6. Unauthorized access (no token)
    status, res = request("POST", "/api/maintenance", {
        "vehicle_id": 1,
        "category": "Oil Change",
        "description": "Unauthorized attempt",
        "scheduled_date": "2026-10-10T10:00:00"
    })
    assert status in [401, 403], f"Expected 401/403 for unauthorized access, got {status}: {res}"
    print(f"[PASS] Unauthorized access returns {status}")

    # 7. Driver vehicle assignment: Missing driver
    status, res = request("POST", "/api/drivers/999999/assign-vehicle", {"vehicle_id": 1}, token=token)
    assert status == 404, f"Expected 404 for missing driver, got {status}: {res}"
    print(f"[PASS] Missing driver assignment returns 404: {res.get('detail')}")

    # 8. Driver vehicle assignment: Missing vehicle
    status, res = request("POST", "/api/drivers/1/assign-vehicle", {"vehicle_id": 999999}, token=token)
    assert status == 404, f"Expected 404 for missing vehicle assignment, got {status}: {res}"
    print(f"[PASS] Missing vehicle assignment returns 404: {res.get('detail')}")

    # 9. Driver vehicle assignment: Assigning vehicle under Maintenance
    # Put vehicle 1 into Maintenance
    request("PUT", "/api/vehicles/1/status", {"current_status": "Maintenance"}, token=token)
    status, res = request("POST", "/api/drivers/1/assign-vehicle", {"vehicle_id": 1}, token=token)
    assert status == 400, f"Expected 400 for maintenance vehicle assignment, got {status}: {res}"
    print(f"[PASS] Assigning vehicle under Maintenance blocked with 400: {res.get('detail')}")
    # Restore vehicle 1 to Available
    request("PUT", "/api/vehicles/1/status", {"current_status": "Available"}, token=token)

    # 10. Negative cost values handled gracefully (floored to 0.0 or validated)
    status, res = request("POST", "/api/maintenance", {
        "vehicle_id": 1,
        "category": "Oil Change",
        "description": "Negative cost test",
        "scheduled_date": "2026-10-10T10:00:00",
        "cost": -500.0
    }, token=token)
    assert status in [200, 201], f"Negative cost failed: {res}"
    assert res.get("cost") >= 0.0, f"Negative cost was not floored: {res.get('cost')}"
    print(f"[PASS] Negative cost sanitized to non-negative: {res.get('cost')}")

    # 11. Invalid Celery task status ID
    status, res = request("GET", "/api/tasks/invalid-uuid-format-12345/status", token=token)
    assert status == 200, f"Celery task check failed: {res}"
    assert res.get("status") in ["PENDING", "UNKNOWN"], f"Unexpected celery task status: {res}"
    print(f"[PASS] Invalid Celery task returns gracefully: {res.get('status')}")

    print("\nALL RULE 22 EDGE CASES & ERROR HANDLING TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_edge_cases()
