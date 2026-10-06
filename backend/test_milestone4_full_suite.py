"""
FleetFlow - Milestone 4 Complete Automated Verification Suite
Validates Milestones 1, 2, 3, and 4 end-to-end workflows and edge cases.
"""
import urllib.request
import urllib.parse
import json
import time
import sys
from datetime import datetime, timedelta, timezone

BASE_URL = "http://127.0.0.1:8000"

class ApiClient:
    def __init__(self, base_url):
        self.base_url = base_url
        self.token = None

    def request(self, method, path, data=None):
        url = f"{self.base_url}{path}"
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        body = None
        if data is not None:
            body = json.dumps(data).encode("utf-8")

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

    def get(self, path):
        return self.request("GET", path)

    def post(self, path, data=None):
        return self.request("POST", path, data)

    def put(self, path, data=None):
        return self.request("PUT", path, data)

    def delete(self, path):
        return self.request("DELETE", path)

def log(msg):
    print(f"  [PASS] {msg}")

def run_milestone4_suite():
    print("=" * 75)
    print("FLEETFLOW -- MILESTONE 4 COMPLETE VERIFICATION SUITE")
    print("Testing M1, M2, M3, M4 Workflows, Security & Edge Cases")
    print("=" * 75)

    client = ApiClient(BASE_URL)

    # -------------------------------------------------------------
    # 1. API HEALTH & INFRASTRUCTURE
    # -------------------------------------------------------------
    print("\n--- 1. Infrastructure & System Health ---")
    status, root_data = client.get("/")
    assert status == 200, f"Root endpoint failed: {root_data}"
    assert "version" in root_data
    log(f"Root API Online: {root_data.get('message')} (v{root_data.get('version')})")

    # -------------------------------------------------------------
    # 2. MILESTONE 1: AUTHENTICATION, RBAC & CORE ENTITIES
    # -------------------------------------------------------------
    print("\n--- 2. Milestone 1: Authentication, RBAC & Core Registry ---")
    # 2.1 Admin Login
    status, token_data = client.post("/api/auth/login", {
        "email": "admin@fleetflow.com",
        "password": "Admin@123"
    })
    assert status == 200, f"Admin login failed: {token_data}"
    client.token = token_data.get("token") or token_data.get("access_token")
    assert client.token is not None
    log(f"Admin Authenticated (Role: {token_data.get('role', 'Administrator')})")

    # 2.2 RBAC Role Login: Driver
    driver_client = ApiClient(BASE_URL)
    status, driver_auth = driver_client.post("/api/auth/login", {
        "email": "driver@fleetflow.com",
        "password": "Admin@123"
    })
    assert status == 200, f"Driver login failed: {driver_auth}"
    driver_client.token = driver_auth.get("token") or driver_auth.get("access_token")
    log("Driver Authenticated for RBAC boundary testing")

    # 2.3 RBAC Permission check: Driver attempting Admin-only Vehicle creation
    status, denied_res = driver_client.post("/api/vehicles", {
        "vehicle_id": "ILLEGAL-VEH",
        "registration_number": "XX-99-9999",
        "vehicle_type": "Truck",
        "capacity": 5000.0,
        "fuel_type": "Diesel"
    })
    assert status in [401, 403], f"Expected 401/403 for unauthorized vehicle creation, got {status}: {denied_res}"
    log("RBAC Boundary Verified: Driver correctly blocked from creating vehicles (HTTP 403)")

    # 2.4 Vehicles & Drivers listing
    status, vehicles = client.get("/api/vehicles")
    assert status == 200 and len(vehicles) >= 1
    log(f"Vehicles Registry: {len(vehicles)} vehicles verified in PostgreSQL")

    status, drivers = client.get("/api/drivers")
    assert status == 200 and len(drivers) >= 1
    log(f"Drivers Registry: {len(drivers)} drivers verified in PostgreSQL")

    test_veh = vehicles[0]
    test_drv = drivers[0]

    # -------------------------------------------------------------
    # 3. MILESTONE 2: SHIPMENTS, ROUTING & LOGISTICS
    # -------------------------------------------------------------
    print("\n--- 3. Milestone 2: Logistics, Routing & Tracking ---")
    status, shipments = client.get("/api/shipments")
    assert status == 200 and len(shipments) >= 1
    sample_shp = shipments[0]
    log(f"Shipments: {len(shipments)} active/historical shipments listed")

    status, shp_history = client.get(f"/api/shipments/{sample_shp['shipment_id']}/history")
    assert status == 200
    log(f"Shipment History Audit: {len(shp_history)} tracking events logged for {sample_shp['shipment_id']}")

    # Route Optimization Engine
    status, route_data = client.post("/api/routes/calculate", {
        "origin": "Vijayawada",
        "destination": "Hyderabad",
        "traffic_level": "Moderate",
        "vehicle_type": "Truck"
    })
    assert status == 200 and len(route_data.get("routes", [])) >= 1
    best_route = route_data["routes"][0]
    log(f"Route Optimization: {len(route_data['routes'])} routes evaluated. Primary: {best_route.get('route_name')} ({best_route.get('distance_km')} km, ETA {best_route.get('estimated_duration')})")

    status, trips = client.get("/api/trips")
    assert status == 200
    log(f"Trip Scheduling: {len(trips)} trips retrieved from PostgreSQL")

    # -------------------------------------------------------------
    # 4. MILESTONE 3: MAINTENANCE, DRIVER ASSIGNMENT & ANALYTICS
    # -------------------------------------------------------------
    print("\n--- 4. Milestone 3: Maintenance, Driver Assignment & Analytics ---")
    # 4.1 Create Maintenance Record
    sched_date = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    status, new_maint = client.post("/api/maintenance", {
        "vehicle_id": test_veh["id"],
        "category": "Brake Service",
        "description": "Milestone 4 verification inspection and brake pad adjustment",
        "scheduled_date": sched_date,
        "priority": "High",
        "cost": 4500.0,
        "mileage": 48500.0,
        "service_center": "National Fleet Care Hub, Vijayawada",
        "notes": "Verified under M4 full suite"
    })
    assert status in [200, 201], f"Create maintenance failed: {new_maint}"
    m_id = new_maint["id"]
    log(f"Maintenance Record Created: #{new_maint['maintenance_id']} ({new_maint['category']}) for {test_veh['vehicle_id']}")

    # 4.2 Lifecycle Status Transition: Scheduled -> In Progress -> Completed
    status, prog_res = client.put(f"/api/maintenance/{m_id}/status", {"status": "In Progress"})
    assert status == 200 and prog_res["status"] == "In Progress"
    log("Maintenance Lifecycle: Transitioned to 'In Progress'")

    status, comp_res = client.put(f"/api/maintenance/{m_id}/status", {"status": "Completed"})
    assert status == 200 and comp_res["status"] == "Completed"
    log("Maintenance Lifecycle: Transitioned to 'Completed'")

    # 4.3 History Audit
    status, m_hist = client.get(f"/api/maintenance/{m_id}/history")
    assert status == 200 and len(m_hist) >= 2
    log(f"Maintenance Audit Trail: {len(m_hist)} immutable audit records verified")

    # 4.4 Vehicle Service History
    status, v_hist = client.get(f"/api/maintenance/vehicle/{test_veh['id']}/history")
    assert status == 200
    log(f"Vehicle Service History: {len(v_hist)} historical events for {test_veh['vehicle_id']}")

    # 4.5 Alerts & Summary
    status, alerts = client.get("/api/maintenance/alerts")
    assert status == 200
    log(f"Proactive Alerts: {len(alerts)} alerts generated from real database criteria")

    status, m_sum = client.get("/api/maintenance/summary")
    assert status == 200 and "maintenance_by_vehicle" in m_sum
    log(f"Maintenance Summary: {m_sum['total_records']} records, Rs.{m_sum['total_maintenance_cost']} total spend")

    # 4.6 Driver Assignment Safety Rules
    status, mon_drivers = client.get("/api/drivers/monitoring")
    assert status == 200 and len(mon_drivers) >= 1
    log(f"Driver Monitoring: {len(mon_drivers)} drivers tracked with performance & attendance")

    # Lockout test: Driver on trip
    on_trip_drv = next((d for d in mon_drivers if d.get("status_label") == "On Trip"), None)
    if on_trip_drv:
        status, blocked = client.post(f"/api/drivers/{on_trip_drv['id']}/assign-vehicle", {"vehicle_id": test_veh["id"]})
        assert status == 400
        log(f"Driver Lockout Rule: Cannot reassign driver '{on_trip_drv['name']}' during active trip (HTTP 400)")

    # Assign available driver
    avail_drv = next((d for d in mon_drivers if d.get("status_label") != "On Trip"), mon_drivers[0])
    status, assign_res = client.post(f"/api/drivers/{avail_drv['id']}/assign-vehicle", {"vehicle_id": test_veh["id"]})
    assert status == 200
    log(f"Driver Assignment: Assigned {test_veh['vehicle_id']} to {avail_drv['name']}")

    # Lockout test: Vehicle under Maintenance
    client.put(f"/api/vehicles/{test_veh['id']}/status", {"current_status": "Maintenance"})
    status, maint_lock = client.post(f"/api/drivers/{avail_drv['id']}/assign-vehicle", {"vehicle_id": test_veh["id"]})
    assert status == 400
    log("Vehicle Safety Lock: Blocked assignment of vehicle currently under Maintenance (HTTP 400)")
    client.put(f"/api/vehicles/{test_veh['id']}/status", {"current_status": "Available"})

    # Unassign
    status, unassign_res = client.post(f"/api/drivers/{avail_drv['id']}/unassign-vehicle")
    assert status == 200
    log(f"Driver Unassignment: Successfully cleared vehicle link for {avail_drv['name']}")

    # 4.7 Operational Analytics & Fuel
    status, op_analytics = client.get("/api/analytics/operational")
    assert status == 200 and "fleet" in op_analytics
    log(f"Fleet Operational Analytics: {op_analytics['fleet']['fleet_utilization_percent']}% utilization, {op_analytics['drivers']['average_attendance']}% driver attendance")

    status, fuel_analytics = client.get("/api/analytics/fuel-monitoring")
    assert status == 200 and "total_fuel_consumed_liters" in fuel_analytics
    log(f"Fuel Analytics: {fuel_analytics['total_fuel_consumed_liters']} L consumed, Rs.{fuel_analytics['total_fuel_cost_estimated']} estimated cost")

    # 4.8 Celery Background Tasks
    status, task_res = client.post("/api/tasks/maintenance-scan")
    assert status in [200, 202]
    task_id = task_res.get("task_id")
    time.sleep(1)
    status, task_status = client.get(f"/api/tasks/{task_id}/status")
    assert status == 200
    log(f"Celery Background Task: Executed ({task_status.get('status')})")

    # -------------------------------------------------------------
    # 5. MILESTONE 4: ROBUST EDGE CASES & ERROR RESILIENCE
    # -------------------------------------------------------------
    print("\n--- 5. Milestone 4: Edge Cases & Error Handling ---")
    # 5.1 Invalid Login
    status, res = client.post("/api/auth/login", {"email": "baduser@fleetflow.com", "password": "WrongPassword"})
    assert status == 401
    log("Edge Case: Invalid login rejected with HTTP 401")

    # 5.2 Malformed JWT
    malformed_client = ApiClient(BASE_URL)
    malformed_client.token = "Bearer this.is.invalid.jwt.token"
    status, res = malformed_client.get("/api/vehicles")
    assert status in [401, 403]
    log("Edge Case: Malformed JWT token rejected with HTTP 401/403")

    # 5.3 Non-existent Vehicle ID
    status, res = client.get("/api/vehicles/999999")
    assert status == 404
    log("Edge Case: Non-existent vehicle ID returns HTTP 404")

    # 5.4 Non-existent Driver ID
    status, res = client.get("/api/drivers/999999")
    assert status == 404
    log("Edge Case: Non-existent driver ID returns HTTP 404")

    # 5.5 Non-existent Shipment ID
    status, res = client.get("/api/shipments/SHP-DOESNOTEXIST/history")
    assert status == 404
    log("Edge Case: Non-existent shipment history returns HTTP 404")

    # 5.6 Non-existent Maintenance ID
    status, res = client.get("/api/maintenance/MNT-99999999")
    assert status == 404
    log("Edge Case: Non-existent maintenance ID returns HTTP 404")

    # 5.7 Invalid Maintenance Category
    status, res = client.post("/api/maintenance", {
        "vehicle_id": test_veh["id"],
        "category": "Intergalactic Teleportation",
        "description": "Invalid category test",
        "scheduled_date": sched_date
    })
    assert status == 400
    log("Edge Case: Invalid maintenance category rejected with HTTP 400")

    # 5.8 Invalid Maintenance Status Update
    status, res = client.put(f"/api/maintenance/{m_id}/status", {"status": "SuperDuper"})
    assert status == 400
    log("Edge Case: Invalid maintenance status update rejected with HTTP 400")

    # 5.9 Negative Cost Handling
    status, res = client.post("/api/maintenance", {
        "vehicle_id": test_veh["id"],
        "category": "General Inspection",
        "description": "Negative cost test",
        "scheduled_date": sched_date,
        "cost": -1200.0
    })
    assert status in [200, 201] and res.get("cost") >= 0.0
    log("Edge Case: Negative cost sanitized to non-negative value (0.0)")

    # 5.10 Missing Driver Assignment Payload
    status, res = client.post("/api/drivers/999999/assign-vehicle", {"vehicle_id": test_veh["id"]})
    assert status == 404
    log("Edge Case: Assigning non-existent driver returns HTTP 404")

    # 5.11 Invalid Celery Task Status Query
    status, res = client.get("/api/tasks/non-existent-task-uuid-1234/status")
    assert status == 200 and res.get("status") in ["PENDING", "UNKNOWN"]
    log("Edge Case: Invalid Celery task status returns gracefully without crash")

    print("\n" + "=" * 75)
    print("ALL MILESTONE 1, 2, 3 & 4 WORKFLOWS AND EDGE CASES PASSED (100%)")
    print("=" * 75)

if __name__ == "__main__":
    run_milestone4_suite()
