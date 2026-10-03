import urllib.request
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

def request(method, path, data=None, token=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as res:
            raw = res.read().decode("utf-8")
            return res.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"detail": raw}

def test_all():
    print("==============================================================")
    print("FLEETFLOW MILESTONE 2 COMPREHENSIVE END-TO-END TEST SUITE")
    print("==============================================================")

    # 1. Test Root
    st, root = request("GET", "/")
    assert st == 200, f"Root failed: {st}"
    print(f"[PASS] Root Endpoint: {root['message']} (Milestone {root['milestone']})")

    # 2. Test All 4 RBAC Roles Authentication
    roles_tested = [
        ("admin@fleetflow.com", "Administrator"),
        ("manager@fleetflow.com", "Fleet Manager"),
        ("dispatcher@fleetflow.com", "Dispatcher"),
        ("driver@fleetflow.com", "Driver")
    ]
    tokens = {}
    for email, expected_role in roles_tested:
        st, res = request("POST", "/api/auth/login", {"email": email, "password": "Admin@123"})
        assert st == 200, f"Login failed for {email}: {st} {res}"
        assert res["role"] == expected_role, f"Role mismatch for {email}: got {res['role']}, expected {expected_role}"
        tokens[expected_role] = res["access_token"]
        print(f"[PASS] Authenticated: {expected_role} ({email})")

    admin_token = tokens["Administrator"]
    manager_token = tokens["Fleet Manager"]
    disp_token = tokens["Dispatcher"]
    driver_token = tokens["Driver"]

    # 3. Test RBAC Write Security (Driver must be forbidden from creating vehicles)
    st, res = request("POST", "/api/vehicles", {
        "vehicle_id": "VH-FORBIDDEN",
        "registration_number": "REG-FORBIDDEN",
        "vehicle_type": "Truck",
        "capacity": 10,
        "fuel_type": "Diesel"
    }, driver_token)
    assert st == 403, f"Driver should get 403 on vehicle creation, got {st}"
    print("[PASS] RBAC Write Protection: Driver was correctly restricted (HTTP 403) from creating vehicles.")

    # 4. Test Vehicle & Driver Retrieval
    st, vehicles = request("GET", "/api/vehicles", token=admin_token)
    assert st == 200, f"Failed to list vehicles: {st}"
    st, drivers = request("GET", "/api/drivers", token=admin_token)
    assert st == 200, f"Failed to list drivers: {st}"
    print(f"[PASS] Fleet Resources: {len(vehicles)} vehicles, {len(drivers)} drivers available in database.")

    # 5. Test Route Optimization Engine
    st, routes_data = request("POST", "/api/routes/calculate", {
        "origin": "Vijayawada",
        "destination": "Hyderabad",
        "traffic_level": "High",
        "vehicle_type": "Truck"
    }, token=manager_token)
    assert st == 200, f"Route optimization failed: {st}"
    assert len(routes_data["routes"]) == 4, f"Expected 4 routes, got {len(routes_data['routes'])}"
    print(f"[PASS] Route Optimizer: 4 alternatives calculated for Vijayawada -> Hyderabad (Traffic: High). Recommended: '{routes_data['recommended_route']}'.")
    for r in routes_data["routes"]:
        print(f"   - {r['route_type']}: {r['distance_km']} km | {r['duration_text']} | Fuel: {r['fuel_estimate_liters']} L")

    # 6. Test Shipment Creation
    st, new_shipment = request("POST", "/api/shipments", {
        "origin": "Vijayawada",
        "destination": "Visakhapatnam",
        "customer_name": "Godavari Industrial Exports",
        "customer_phone": "+91 99887 76655",
        "description": "Critical heavy machinery parts",
        "route_type": "Fastest Route",
        "traffic_level": "Moderate"
    }, token=disp_token)
    assert st == 201, f"Shipment creation failed: {st} {new_shipment}"
    shp_id = new_shipment["shipment_id"]
    trk_num = new_shipment["tracking_number"]
    print(f"[PASS] Shipment Created: {shp_id} (Tracking: {trk_num}) | Distance: {new_shipment['distance_km']} km | Status: {new_shipment['status']}")

    # 7. Test Asset Assignment
    st, assigned_shp = request("POST", f"/api/shipments/{shp_id}/assign", {
        "vehicle_id": vehicles[0]["id"],
        "driver_id": drivers[0]["id"]
    }, token=disp_token)
    assert st == 200, f"Assignment failed: {st}"
    assert assigned_shp["status"] == "Assigned"
    print(f"[PASS] Asset Assignment: Vehicle {vehicles[0]['vehicle_id']} and Driver {drivers[0]['name']} linked. Status -> '{assigned_shp['status']}'")

    # 8. Test Simulated GPS Telemetry Progression
    for step in range(1, 4):
        st, sim_step = request("POST", f"/api/tracking/{shp_id}/simulate-step", token=driver_token)
        assert st == 200, f"Simulation step {step} failed: {st}"
        print(f"[PASS] Simulated GPS Telemetry Step {step}: Progress: {sim_step['progress']}% | Status: '{sim_step['status']}' | Location: {sim_step['location_name']} | Remaining: {sim_step['remaining_km']} km")

    # 9. Test Querying Live Telemetry & ETA
    st, telemetry = request("GET", f"/api/tracking/{shp_id}", token=admin_token)
    assert st == 200, f"Telemetry query failed: {st}"
    assert "GPS" in telemetry["gps_status"]
    print(f"[PASS] Live Telemetry Stream: GPS Status: '{telemetry['gps_status']}' | Current Lat/Lng: ({telemetry['latitude']}, {telemetry['longitude']}) | ETA: {telemetry['eta']}")

    # 10. Test Audit History Trail
    st, history_events = request("GET", f"/api/shipments/{shp_id}/history", token=admin_token)
    assert st == 200, f"History query failed: {st}"
    assert len(history_events) >= 4, f"Expected at least 4 events in audit trail, got {len(history_events)}"
    print(f"[PASS] Audit Trail: {len(history_events)} events successfully logged for shipment {shp_id}.")

    # 11. Test Trip Scheduling & Asset Conflict Prevention
    st, active_trips = request("GET", "/api/trips", token=manager_token)
    for at in active_trips:
        if at.get("trip_status") in ["Started", "In Transit"]:
            request("PUT", f"/api/trips/{at['trip_id']}/status", {"trip_status": "Completed"}, token=manager_token)

    st, scheduled_trip = request("POST", "/api/trips", {
        "origin": "Vijayawada",
        "destination": "Visakhapatnam",
        "vehicle_id": vehicles[1]["id"] if len(vehicles) > 1 else vehicles[0]["id"],
        "driver_id": drivers[0]["id"],
        "route_type": "Fastest Route",
        "notes": "Milestone 2 scheduled departure"
    }, token=manager_token)
    assert st == 201, f"Trip creation failed: {st} {scheduled_trip}"
    trip_id = scheduled_trip["trip_id"]
    print(f"[PASS] Trip Scheduled: {trip_id} (Corridor: {scheduled_trip['origin']} -> {scheduled_trip['destination']})")

    # Start the trip
    st, started_trip = request("PUT", f"/api/trips/{trip_id}/status", {"trip_status": "In Transit"}, token=manager_token)
    assert st == 200, f"Trip status update failed: {st}"
    print(f"[PASS] Trip In-Transit: Status -> '{started_trip['trip_status']}'")

    # Test conflict: attempt to schedule another trip with the SAME vehicle while in transit
    st, conflict_trip = request("POST", "/api/trips", {
        "origin": "Guntur",
        "destination": "Hyderabad",
        "vehicle_id": scheduled_trip["vehicle_id"],
        "driver_id": drivers[0]["id"]
    }, token=manager_token)
    assert st == 409, f"Expected conflict 409, got {st}: {conflict_trip}"
    print(f"[PASS] Conflict Prevention: Conflicting assignment correctly blocked with HTTP 409: '{conflict_trip['detail']}'")

    # 12. Test Extended Dashboard Summary
    st, dash = request("GET", "/api/dashboard/summary", token=admin_token)
    assert st == 200, f"Dashboard summary failed: {st}"
    print("[PASS] Dashboard Aggregations (Real PostgreSQL Data):")
    print(f"   * Fleet: {dash['total_vehicles']} Vehicles ({dash['available_vehicles']} Available, {dash['active_vehicles']} Active)")
    print(f"   * Drivers: {dash['active_drivers']} Active Drivers")
    print(f"   * Shipments: {dash['total_shipments']} Total ({dash['active_shipments']} Active, {dash['in_transit_shipments']} In Transit, {dash['delivered_shipments']} Delivered)")
    print(f"   * Trips: {dash['active_trips']} Active In-Transit Trips")
    print(f"   * Operational Activity Feed: {len(dash['recent_shipments'])} live items")

    print("==============================================================")
    print("ALL MILESTONE 2 REQUIREMENTS VERIFIED AND FUNCTIONAL!")
    print("==============================================================")

if __name__ == "__main__":
    test_all()
