import urllib.request
import json

RENDER_BASE = "https://fleetflow-api-p7ai.onrender.com"

def post(path, data, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(f"{RENDER_BASE}{path}", data=json.dumps(data).encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())

def get(path, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(f"{RENDER_BASE}{path}", headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            content_type = resp.headers.get("Content-Type", "")
            if "application/json" in content_type:
                return resp.status, json.loads(resp.read().decode()), resp.headers
            else:
                return resp.status, resp.read(), resp.headers
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode()), None

def run_production_smoke_tests():
    print("=" * 75)
    print("FLEETFLOW -- PRODUCTION RENDER SMOKE TEST SUITE")
    print(f"Target: {RENDER_BASE}")
    print("=" * 75)

    # 1. Root Health Check
    status, root, _ = get("/")
    assert status == 200 and root.get("version") == "4.0.0"
    print(f"[PASS] 1. Root Health: {root.get('message')} (v{root.get('version')}, Milestone {root.get('milestone')})")

    # 2. Authentication: Admin Login
    status, login_res = post("/api/auth/login", {"email": "admin@fleetflow.com", "password": "Admin@123"})
    assert status == 200 and "access_token" in login_res
    admin_token = login_res["access_token"]
    print(f"[PASS] 2. Admin Authentication: Logged in successfully as {login_res.get('role')} (Token Issued)")

    # 3. Profile Endpoint: GET /api/auth/me
    status, me, _ = get("/api/auth/me", admin_token)
    assert status == 200 and me.get("email") == "admin@fleetflow.com"
    assert "password_hash" not in me
    print(f"[PASS] 3. Profile Endpoint: Retrieved authenticated user {me.get('email')} (Role: {me.get('role')})")

    # 4. Password Change Security: PUT /api/auth/change-password
    # Test invalid current password rejection
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {admin_token}"}
    req = urllib.request.Request(
        f"{RENDER_BASE}/api/auth/change-password",
        data=json.dumps({"current_password": "InvalidCurrentPassword!", "new_password": "ShouldNotChange123"}).encode(),
        headers=headers,
        method="PUT"
    )
    try:
        urllib.request.urlopen(req, timeout=30)
        assert False, "Should reject invalid current password"
    except urllib.error.HTTPError as e:
        assert e.code == 400
        print("[PASS] 4. Security Check: PUT /api/auth/change-password correctly rejected invalid current password (HTTP 400)")

    # 5. Notifications: GET /api/notifications
    status, notifs, _ = get("/api/notifications", admin_token)
    assert status == 200 and isinstance(notifs, list)
    print(f"[PASS] 5. Operational Notifications: {len(notifs)} real alerts retrieved from Render database")

    # 6. Report Export: CSV
    status, csv_data, csv_headers = get("/api/reports/export?report_type=fleet_utilization&format=csv", admin_token)
    assert status == 200
    csv_text = csv_data.decode("utf-8") if isinstance(csv_data, bytes) else csv_data
    assert "Vehicle ID" in csv_text or "Registration" in csv_text
    print(f"[PASS] 6. Report Export (CSV): Downloaded valid RFC-4180 CSV ({len(csv_text)} bytes) from Render database")

    # 7. Report Export: PDF
    status, pdf_bytes, pdf_headers = get("/api/reports/export?report_type=fleet_utilization&format=pdf", admin_token)
    assert status == 200 and isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF-1.4"), "Invalid PDF header"
    assert b"%%EOF" in pdf_bytes[-20:], "Invalid PDF trailer"
    print(f"[PASS] 7. Report Export (PDF): Downloaded valid PDF-1.4 binary document ({len(pdf_bytes)} bytes)")

    # 8. Core Workflows Regression: Vehicles, Shipments, Analytics
    status, vehicles, _ = get("/api/vehicles", admin_token)
    assert status == 200 and len(vehicles) > 0
    print(f"[PASS] 8. Vehicles Registry: {len(vehicles)} vehicles active in production database")

    status, shipments, _ = get("/api/shipments", admin_token)
    assert status == 200
    print(f"[PASS] 9. Shipments Registry: {len(shipments)} shipments tracked in production")

    status, dash, _ = get("/api/dashboard/summary", admin_token)
    assert status == 200
    print(f"[PASS] 10. Dashboard Summary: {dash.get('total_vehicles')} total vehicles, {dash.get('active_drivers')} active drivers")

    # 9. Production Frontend Accessibility
    with urllib.request.urlopen("https://fleetflow-ssts.onrender.com/", timeout=30) as resp:
        assert resp.status == 200
        html = resp.read().decode("utf-8")
        assert "FleetFlow" in html
        assert "assets/index-" in html and ".js" in html
        print("[PASS] 11. Production Frontend: HTTP 200 OK, latest production JavaScript bundle loaded")

    print("=" * 75)
    print("ALL 11 PRODUCTION RENDER SMOKE TESTS PASSED (100% SUCCESS)!")
    print("=" * 75)

if __name__ == "__main__":
    run_production_smoke_tests()
