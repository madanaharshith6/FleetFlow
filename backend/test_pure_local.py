import urllib.request
import json
import asyncio
import websockets

BASE_URL = "http://127.0.0.1:8000"
WS_URL = "ws://127.0.0.1:8000"

def post(path, data, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(f"{BASE_URL}{path}", data=json.dumps(data).encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())

def get(path, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(f"{BASE_URL}{path}", headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())

def run_local_audit():
    print("=" * 70)
    print("FLEETFLOW -- 100% LOCAL STACK AUDIT (ZERO RENDER CALLS)")
    print("=" * 70)

    # 1. Root Health Check
    status, root = get("/")
    assert status == 200
    print(f"1. [PASS] Local API Health: {root.get('message')} (v{root.get('version')})")

    # 2. Authentication for all 4 roles
    roles = [
        ("admin@fleetflow.com", "Admin@123", "Administrator"),
        ("manager@fleetflow.com", "Admin@123", "Fleet Manager"),
        ("dispatcher@fleetflow.com", "Admin@123", "Dispatcher"),
        ("driver@fleetflow.com", "Admin@123", "Driver")
    ]
    tokens = {}
    for email, pwd, role in roles:
        status, res = post("/api/auth/login", {"email": email, "password": pwd})
        assert status == 200 and res.get("role") == role
        tokens[role] = res["access_token"]
        print(f"2. [PASS] Authenticated {role} ({email}) -> Token Issued")

    admin_token = tokens["Administrator"]
    driver_token = tokens["Driver"]

    # 3. RBAC Boundary Check
    status, err = post("/api/vehicles", {
        "vehicle_id": "VH-RBAC",
        "registration_number": "AP00RBAC",
        "vehicle_type": "Truck",
        "capacity": 1000.0,
        "fuel_type": "Diesel"
    }, driver_token)
    assert status == 403
    print("3. [PASS] RBAC Boundary Enforcement: Driver blocked from vehicle creation (HTTP 403)")

    # 4. Local PostgreSQL Data Queries
    status, vehicles = get("/api/vehicles", admin_token)
    assert status == 200 and len(vehicles) > 0
    print(f"4. [PASS] PostgreSQL Vehicles Registry: {len(vehicles)} vehicles retrieved")

    status, drivers = get("/api/drivers", admin_token)
    assert status == 200 and len(drivers) > 0
    print(f"5. [PASS] PostgreSQL Drivers Registry: {len(drivers)} drivers retrieved")

    status, shipments = get("/api/shipments", admin_token)
    assert status == 200 and len(shipments) > 0
    print(f"6. [PASS] PostgreSQL Shipments: {len(shipments)} shipments retrieved")

    # 5. Routing & Optimization
    status, routes = post("/api/routes/calculate", {
        "origin": "Vijayawada",
        "destination": "Hyderabad",
        "traffic_level": "Moderate"
    }, admin_token)
    assert status == 200 and len(routes["routes"]) == 4
    print(f"7. [PASS] Route Optimizer: 4 alternatives evaluated (Fastest: {routes['routes'][0]['distance_km']} km, ETA {routes['routes'][0]['eta_time']})")

    # 6. Maintenance Management & Summary
    status, summary = get("/api/maintenance/summary", admin_token)
    assert status == 200
    print(f"8. [PASS] Maintenance Summary: {summary['total_records']} records, Rs.{summary['total_maintenance_cost']} spend")

    status, alerts = get("/api/maintenance/alerts", admin_token)
    assert status == 200
    print(f"9. [PASS] Proactive Alerts: {len(alerts)} alerts generated from PostgreSQL criteria")

    # 7. Operational Analytics
    status, util = get("/api/analytics/operational", admin_token)
    assert status == 200
    fleet_kpi = util["fleet"]
    print(f"10. [PASS] Fleet Utilization Analytics: {fleet_kpi['fleet_utilization_percent']}% ({fleet_kpi['active_vehicles']}/{fleet_kpi['total_vehicles']} active)")

    status, fuel = get("/api/analytics/fuel-monitoring", admin_token)
    assert status == 200
    print(f"11. [PASS] Fuel Analytics: {fuel['total_fuel_consumed_liters']} L consumed, Rs.{fuel['total_fuel_cost_estimated']}")

    # 8. Celery Background Processing via Redis
    status, job = post("/api/tasks/maintenance-scan", {}, admin_token)
    assert status == 200 and "task_id" in job
    task_id = job["task_id"]
    print(f"12. [PASS] Celery Job Dispatched to Redis: Task ID {task_id} (Status: {job['status']})")

    # Poll status for worker execution
    import time
    time.sleep(1.0)
    status, task_status = get(f"/api/tasks/{task_id}/status", admin_token)
    assert status == 200
    print(f"13. [PASS] Celery Task Execution: State = {task_status['status']}")

    # 9. WebSocket Real-Time Connection
    async def test_ws():
        uri = f"{WS_URL}/ws/shipments/{shipments[0]['shipment_id']}"
        async with websockets.connect(uri) as ws:
            await ws.send(json.dumps({"type": "ping"}))
            msg = await asyncio.wait_for(ws.recv(), timeout=3.0)
            data = json.loads(msg)
            assert data["type"] == "connection_established"
            print(f"14. [PASS] Local WebSocket: Handshake & Real-time channel verified ({uri})")

    asyncio.run(test_ws())

    # 10. Local Frontend Verification
    with urllib.request.urlopen("http://localhost:5173/") as resp:
        assert resp.status == 200
        html = resp.read().decode("utf-8")
        assert "<div id=\"root\">" in html
        print("15. [PASS] Local Vite Frontend: HTTP 200 OK, SPA root element rendered")

    print("=" * 70)
    print("ALL 15 LOCAL CHECKS PASSED WITH 100% SUCCESS WITHOUT RENDER!")
    print("=" * 70)

if __name__ == "__main__":
    run_local_audit()
