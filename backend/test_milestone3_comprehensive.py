"""
Comprehensive Milestone 3 Test Suite for FleetFlow
Tests all Milestone 3 features end-to-end using standard library urllib.
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
        return self.request("POST", path, data=data or {})

    def put(self, path, data=None):
        return self.request("PUT", path, data=data or {})

    def delete(self, path):
        return self.request("DELETE", path)

def log(msg, success=True):
    symbol = "PASS" if success else "FAIL"
    print(f"[{symbol}] {msg}")

def main():
    print("=" * 70)
    print("FLEETFLOW -- COMPREHENSIVE MILESTONE 3 VERIFICATION SUITE")
    print("=" * 70)

    client = ApiClient(BASE_URL)

    # 1. AUTHENTICATION & LOGIN
    print("\n--- 1. Authentication & RBAC ---")
    status, token_data = client.post("/api/auth/login", {
        "email": "admin@fleetflow.com",
        "password": "Admin@123"
    })
    assert status == 200, f"Login failed: {token_data}"
    client.token = token_data.get("token") or token_data.get("access_token")
    log(f"Authenticated as Admin (Role: {token_data.get('role', 'Administrator')})")

    # 2. MILESTONE 1 REGRESSION: VEHICLES & DRIVERS
    print("\n--- 2. Milestone 1 Regression Checks ---")
    status, vehicles = client.get("/api/vehicles")
    assert status == 200, f"Get vehicles failed: {vehicles}"
    assert len(vehicles) >= 1, "Expected at least 1 vehicle"
    log(f"Milestone 1 Vehicles: {len(vehicles)} vehicles registered")

    status, drivers = client.get("/api/drivers")
    assert status == 200, f"Get drivers failed: {drivers}"
    assert len(drivers) >= 1, "Expected at least 1 driver"
    log(f"Milestone 1 Drivers: {len(drivers)} drivers registered")

    # 3. MILESTONE 2 REGRESSION: SHIPMENTS, ROUTE OPTIMIZATION, TRIPS
    print("\n--- 3. Milestone 2 Regression Checks ---")
    status, shipments = client.get("/api/shipments")
    assert status == 200, f"Get shipments failed: {shipments}"
    log(f"Milestone 2 Shipments: {len(shipments)} shipments listed")

    status, history = client.get(f"/api/shipments/{shipments[0]['shipment_id']}/history")
    assert status == 200, f"Get shipment history failed: {history}"
    log(f"Milestone 2 History: {len(history)} events logged for {shipments[0]['shipment_id']}")

    status, route_data = client.post("/api/routes/calculate", {
        "origin": "Vijayawada",
        "destination": "Hyderabad",
        "traffic_level": "Moderate",
        "vehicle_type": "Truck"
    })
    assert status == 200, f"Route optimization failed: {route_data}"
    routes_list = route_data.get("routes", [])
    assert len(routes_list) >= 1, "Expected at least 1 calculated route option"
    best = routes_list[0]
    log(f"Milestone 2 Route Optimizer: {len(routes_list)} route options evaluated (Primary: {best.get('route_name')}, {best.get('distance_km')} km, ETA {best.get('estimated_duration')})")

    status, trips = client.get("/api/trips")
    assert status == 200, f"Get trips failed: {trips}"
    log(f"Milestone 2 Trip Scheduling: {len(trips)} scheduled trips verified")

    # 4. MILESTONE 3: VEHICLE MAINTENANCE MANAGEMENT MODULE
    print("\n--- 4. Milestone 3: Maintenance Management Module ---")
    test_veh = vehicles[0]

    # 4.1 Create Maintenance Record
    sched_date = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    create_payload = {
        "vehicle_id": test_veh["id"],
        "category": "Engine Service",
        "description": "Comprehensive 50,000 km engine service and timing belt inspection",
        "scheduled_date": sched_date,
        "priority": "High",
        "cost": 12500.0,
        "mileage": 52300.0,
        "service_center": "Authorized FleetCare Center, Vijayawada",
        "notes": "Original parts certified"
    }
    status, m_record = client.post("/api/maintenance", create_payload)
    assert status in [200, 201], f"Create maintenance failed: {m_record}"
    m_id = m_record["id"]
    log(f"Created Maintenance #{m_record['maintenance_id']} for {test_veh['vehicle_id']} (Category: {m_record['category']}, Cost: Rs.{m_record['cost']})")

    # 4.2 List Maintenance Records
    status, records_list = client.get("/api/maintenance")
    assert status == 200, f"List maintenance failed: {records_list}"
    assert any(r["id"] == m_id for r in records_list), "Created record not found in list"
    log(f"Listed Maintenance Records: {len(records_list)} total records retrieved")

    # 4.3 Get Single Maintenance Record
    status, m_single = client.get(f"/api/maintenance/{m_id}")
    assert status == 200, f"Get maintenance record failed: {m_single}"
    log(f"Fetched Single Maintenance Record #{m_single['maintenance_id']}")

    # 4.4 Status Workflow Lifecycle: Scheduled -> In Progress -> Completed
    print("Testing Maintenance Status Workflow Lifecycle...")
    status, stat1 = client.put(f"/api/maintenance/{m_id}/status", {
        "status": "In Progress",
        "notes": "Vehicle inducted into service bay 3",
        "cost": 13000.0
    })
    assert status == 200, f"Status update to In Progress failed: {stat1}"
    assert stat1["status"] == "In Progress"
    log("Maintenance status transitioned to 'In Progress'")

    status, stat2 = client.put(f"/api/maintenance/{m_id}/status", {
        "status": "Completed",
        "notes": "Service completed and quality check signed off",
        "cost": 13250.0
    })
    assert status == 200, f"Status update to Completed failed: {stat2}"
    assert stat2["status"] == "Completed"
    log("Maintenance status transitioned to 'Completed'")

    # 4.5 Service History Audit Trail
    status, audit_events = client.get(f"/api/maintenance/{m_id}/history")
    assert status == 200, f"Maintenance audit history failed: {audit_events}"
    assert len(audit_events) >= 2, f"Expected at least 2 audit events, got {len(audit_events)}"
    log(f"Maintenance Audit Trail: {len(audit_events)} logged lifecycle events verified")

    # 4.6 Vehicle-Specific Service History
    status, veh_hist = client.get(f"/api/maintenance/vehicle/{test_veh['id']}/history")
    assert status == 200, f"Vehicle maintenance history failed: {veh_hist}"
    log(f"Vehicle Service History: {len(veh_hist)} service records for {test_veh['vehicle_id']}")

    # 4.7 Upcoming & Overdue Filters
    status, up_records = client.get("/api/maintenance/upcoming")
    assert status == 200, f"Upcoming maintenance failed: {up_records}"
    log(f"Upcoming Maintenance: {len(up_records)} services scheduled")

    status, ov_records = client.get("/api/maintenance/overdue")
    assert status == 200, f"Overdue maintenance failed: {ov_records}"
    log(f"Overdue Maintenance: {len(ov_records)} services flagged")

    # 4.8 Proactive Maintenance Alerts
    status, alerts_list = client.get("/api/maintenance/alerts")
    assert status == 200, f"Maintenance alerts failed: {alerts_list}"
    log(f"Maintenance Alerts: {len(alerts_list)} active proactive alerts")

    # 4.9 Maintenance Summary Statistics
    status, sum_data = client.get("/api/maintenance/summary")
    assert status == 200, f"Maintenance summary failed: {sum_data}"
    assert "total_records" in sum_data and "total_maintenance_cost" in sum_data
    log(f"Maintenance Summary: {sum_data['total_records']} total records, Rs.{sum_data['total_maintenance_cost']} total spend, {sum_data['completed_count']} completed")

    # 5. MILESTONE 3: DRIVER ASSIGNMENT SYSTEM & MONITORING
    print("\n--- 5. Milestone 3: Driver Assignment System & Monitoring ---")
    status, mon_drivers = client.get("/api/drivers/monitoring")
    assert status == 200, f"Driver monitoring failed: {mon_drivers}"
    assert len(mon_drivers) >= 1
    log(f"Driver Monitoring: {len(mon_drivers)} drivers tracked")

    # If any driver is On Trip, verify safety rule: cannot reassign driver on active trip
    on_trip_driver = next((d for d in mon_drivers if d.get("status_label") == "On Trip"), None)
    if on_trip_driver:
        status, blocked_res = client.post(f"/api/drivers/{on_trip_driver['id']}/assign-vehicle", {
            "vehicle_id": test_veh["id"]
        })
        assert status == 400, f"Expected 400 when assigning driver on trip, got {status}: {blocked_res}"
        log(f"Safety Rule Verified: Locked reassignment of driver '{on_trip_driver['name']}' currently on trip (HTTP 400)")

    # Find an available driver without active trips
    avail_driver = next((d for d in mon_drivers if d.get("status_label") != "On Trip"), None)
    assert avail_driver is not None, "Expected at least one available driver for assignment testing"

    # Assign vehicle to available driver
    status, assign_res = client.post(f"/api/drivers/{avail_driver['id']}/assign-vehicle", {
        "vehicle_id": test_veh["id"]
    })
    assert status == 200, f"Assign vehicle failed: {assign_res}"
    log(f"Driver Assignment: Assigned {test_veh['vehicle_id']} to {avail_driver['name']}")

    # Verify vehicle status conflict prevention
    # Temporarily set vehicle to Maintenance
    client.put(f"/api/vehicles/{test_veh['id']}/status", {"current_status": "Maintenance"})
    status, maint_conflict = client.post(f"/api/drivers/{avail_driver['id']}/assign-vehicle", {
        "vehicle_id": test_veh["id"]
    })
    assert status == 400, f"Expected 400 when assigning a vehicle under Maintenance, got {status}: {maint_conflict}"
    log("Safety Rule Verified: Locked assignment of vehicle under Maintenance (HTTP 400)")

    # Restore vehicle status to Available
    client.put(f"/api/vehicles/{test_veh['id']}/status", {"current_status": "Available"})

    # Unassign vehicle
    status, unassign_res = client.post(f"/api/drivers/{avail_driver['id']}/unassign-vehicle")
    assert status == 200, f"Unassign vehicle failed: {unassign_res}"
    log(f"Driver Unassignment: Successfully unassigned vehicle from {avail_driver['name']}")

    # 6. MILESTONE 3: OPERATIONAL ANALYTICS WORKFLOWS
    print("\n--- 6. Milestone 3: Operational Analytics Workflows ---")
    status, op_data = client.get("/api/analytics/operational")
    assert status == 200, f"Operational analytics failed: {op_data}"
    assert "fleet" in op_data and "drivers" in op_data and "shipments" in op_data
    log(f"Fleet Utilization: {op_data['fleet']['fleet_utilization_percent']}% (Active: {op_data['fleet']['active_vehicles']}/{op_data['fleet']['total_vehicles']})")
    log(f"Formula Grounding: {op_data['fleet']['utilization_formula']}")
    log(f"Driver Attendance: {op_data['drivers']['average_attendance']}% across {op_data['drivers']['total_drivers']} drivers")
    log(f"Fulfillment Rate: {op_data['shipments']['completion_rate_percent']}% ({op_data['shipments']['delivered_shipments']} delivered)")

    status, util_data = client.get("/api/analytics/fleet-utilization")
    assert status == 200, f"Fleet utilization endpoint failed: {util_data}"
    rate_val = util_data.get('fleet_utilization_percent', util_data.get('utilization_rate_percent'))
    log(f"Dedicated Utilization Endpoint: {rate_val}%")

    # 7. MILESTONE 3: FUEL MONITORING ANALYTICS
    print("\n--- 7. Milestone 3: Fuel Monitoring Analytics ---")
    status, fuel_data = client.get("/api/analytics/fuel-monitoring")
    assert status == 200, f"Fuel analytics failed: {fuel_data}"
    assert "total_fuel_consumed_liters" in fuel_data and "vehicle_rankings" in fuel_data
    log(f"Total Fuel Burned: {fuel_data['total_fuel_consumed_liters']} L (Estimated Cost: Rs.{fuel_data['total_fuel_cost_estimated']})")
    log(f"Average Fleet Efficiency: {fuel_data['average_fleet_efficiency_kpl']} km/L")
    log(f"Ranked Vehicles: {len(fuel_data['vehicle_rankings'])} vehicle powertrain profiles analyzed")

    # 8. MILESTONE 3: CELERY BACKGROUND WORKER JOBS VIA REDIS
    print("\n--- 8. Milestone 3: Celery Background Jobs (Redis Broker) ---")
    
    # 8.1 Scan Overdue Maintenance Task
    status, t1_res = client.post("/api/tasks/maintenance-scan")
    assert status == 200, f"Trigger maintenance scan task failed: {t1_res}"
    t1_id = t1_res["task_id"]
    log(f"Triggered Overdue Scan Task (ID: {t1_id})")

    # Poll status
    time.sleep(1)
    status, status1 = client.get(f"/api/tasks/{t1_id}/status")
    assert status == 200
    assert status1["status"] in ["PENDING", "SUCCESS"], f"Unexpected task status: {status1}"
    log(f"Celery Task 1 Status: {status1['status']} (Result: {status1.get('result')})")

    # 8.2 Maintenance Reminders Task
    status, t2_res = client.post("/api/tasks/maintenance-reminders")
    assert status == 200, f"Trigger reminders task failed: {t2_res}"
    t2_id = t2_res["task_id"]
    time.sleep(1)
    status, status2 = client.get(f"/api/tasks/{t2_id}/status")
    assert status == 200
    log(f"Celery Task 2 Status: {status2['status']} (Result: {status2.get('result')})")

    # 8.3 Fleet Analytics Aggregation Task
    status, t3_res = client.post("/api/tasks/analytics-aggregation")
    assert status == 200, f"Trigger analytics task failed: {t3_res}"
    t3_id = t3_res["task_id"]
    time.sleep(1)
    status, status3 = client.get(f"/api/tasks/{t3_id}/status")
    assert status == 200
    log(f"Celery Task 3 Status: {status3['status']} (Result: {status3.get('result')})")

    # 9. DASHBOARD SUMMARY ENDPOINT (ALL MILESTONES INTEGRATED)
    print("\n--- 9. Integrated Dashboard Summary ---")
    status, dash_data = client.get("/api/dashboard/summary")
    assert status == 200, f"Dashboard summary failed: {dash_data}"
    assert "total_vehicles" in dash_data
    assert "total_shipments" in dash_data
    assert "fleet_utilization_percent" in dash_data
    assert "total_maintenance" in dash_data
    assert "total_fuel_consumed_liters" in dash_data
    log(f"Dashboard Integration: Fleet Utilization {dash_data['fleet_utilization_percent']}%, Total Maintenance {dash_data['total_maintenance']}, Fuel {dash_data['total_fuel_consumed_liters']} L, Recent Alerts {len(dash_data.get('recent_alerts', []))}")

    print("\n" + "=" * 70)
    print("ALL MILESTONE 3 TESTS & REGRESSION CHECKS PASSED SUCCESSFULLY (100%)")
    print("=" * 70)

if __name__ == "__main__":
    main()
