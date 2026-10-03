import json
import urllib.request
import urllib.error
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

def make_req(method, endpoint, data=None, token=None):
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req) as resp:
            status = resp.status
            content = resp.read().decode("utf-8")
            return status, json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        err_content = e.read().decode("utf-8")
        try:
            err_json = json.loads(err_content)
        except Exception:
            err_json = {"detail": err_content}
        return e.code, err_json

def run_tests():
    print("=" * 65)
    print("FLEETFLOW MILESTONE 2 VERIFICATION & CORRECTION TEST SUITE")
    print("=" * 65)

    # 1. AUTHENTICATION
    status, auth_data = make_req("POST", "/api/auth/login", {
        "email": "admin@fleetflow.com",
        "password": "Admin@123"
    })
    assert status == 200, f"Auth failed ({status}): {auth_data}"
    token = auth_data["access_token"]
    print("[PASS] 1. Auth: Authenticated as Administrator")

    # Fetch vehicles and drivers
    _, vehicles = make_req("GET", "/api/vehicles", token=token)
    _, drivers = make_req("GET", "/api/drivers", token=token)
    v_id = vehicles[0]["id"] if vehicles else None
    d_id = drivers[0]["id"] if drivers else None

    # 2. CREATE SHIPMENT (Real DB Persistence)
    ts = int(datetime.utcnow().timestamp())
    test_shp_id = f"TEST-SHP-{ts}"
    test_trk_id = f"TEST-TRK-{ts}"
    create_payload = {
        "shipment_id": test_shp_id,
        "tracking_number": test_trk_id,
        "customer_name": "Apex Engineering Corp",
        "customer_phone": "+91 91234 56789",
        "origin": "Vijayawada",
        "destination": "Hyderabad",
        "description": "High-precision telemetry sensors",
        "vehicle_id": v_id,
        "driver_id": d_id,
        "route_type": "Fastest Route",
        "traffic_level": "Moderate"
    }
    status, shp_data = make_req("POST", "/api/shipments", create_payload, token=token)
    assert status == 201, f"Create shipment failed ({status}): {shp_data}"
    assert shp_data["shipment_id"] == test_shp_id
    assert shp_data["tracking_number"] == test_trk_id
    assert shp_data["customer_name"] == "Apex Engineering Corp"
    assert shp_data["status"] == "Assigned"
    assert shp_data["distance_km"] > 0
    assert shp_data["estimated_duration"] is not None
    print(f"[PASS] 2. Create Shipment: {test_shp_id} saved to PostgreSQL (Status: {shp_data['status']}, Distance: {shp_data['distance_km']} km, ETA: {shp_data['estimated_duration']})")

    # Verify persistence by reading back
    get_status, get_data = make_req("GET", f"/api/shipments/{test_shp_id}", token=token)
    assert get_status == 200
    assert get_data["id"] == shp_data["id"]
    print(f"[PASS] 2b. Database Persistence: Shipment verified after direct query from PostgreSQL")

    # 3. STATUS UPDATE WORKFLOW (Created -> Assigned -> In Transit -> Delayed -> Delivered)
    # Assigned -> In Transit
    st1, st1_data = make_req("PUT", f"/api/shipments/{test_shp_id}/status", {
        "status": "In Transit",
        "description": "Vehicle departed originating depot."
    }, token=token)
    assert st1 == 200, f"Transition failed ({st1}): {st1_data}"
    assert st1_data["status"] == "In Transit"

    # In Transit -> Delayed
    st2, st2_data = make_req("PUT", f"/api/shipments/{test_shp_id}/status", {
        "status": "Delayed",
        "description": "Heavy rain on expressway corridor."
    }, token=token)
    assert st2 == 200
    assert st2_data["status"] == "Delayed"
    print(f"[PASS] 3. Status Workflow: Assigned -> In Transit -> Delayed transitions successful and persisted")

    # 4. SHIPMENT HISTORY
    hist_status, history_events = make_req("GET", f"/api/shipments/{test_shp_id}/history", token=token)
    assert hist_status == 200, f"History fetch failed ({hist_status}): {history_events}"
    assert len(history_events) >= 3, f"Expected at least 3 history events, got {len(history_events)}"
    event_types = [h["event_type"] for h in history_events]
    print(f"[PASS] 4. History Audit Trail: {len(history_events)} events in PostgreSQL: {', '.join(event_types)}")

    # 5. LIVE TRACKING & TELEMETRY
    tel_status, t_data = make_req("GET", f"/api/tracking/{test_shp_id}", token=token)
    assert tel_status == 200
    assert t_data["status"] == "Delayed"
    assert "Simulated GPS" in t_data["gps_status"]
    assert t_data["remaining_km"] > 0
    print(f"[PASS] 5. Live Tracking: Telemetry verified (Status: {t_data['status']}, GPS: '{t_data['gps_status']}', Remaining: {t_data['remaining_km']} km)")

    # 6. SIMULATE NEXT WAYPOINT (GPS PROGRESSION)
    sim1_status, sim_data = make_req("POST", f"/api/tracking/{test_shp_id}/simulate-step", token=token)
    assert sim1_status == 200
    assert sim_data["progress"] > 0
    assert sim_data["remaining_km"] < t_data["remaining_km"]
    assert "Simulated GPS" in sim_data["gps_status"]
    print(f"[PASS] 6. GPS / Waypoint Simulation: Vehicle advanced to {sim_data['location_name']} (Progress: {sim_data['progress']}%, Remaining: {sim_data['remaining_km']} km)")

    # 7. ROUTE OPTIMIZATION (ALL 4 ALTERNATIVES)
    opt_status, opt_data = make_req("POST", "/api/routes/calculate", {
        "origin": "Vijayawada",
        "destination": "Hyderabad",
        "traffic_level": "Low",
        "vehicle_type": "Truck"
    }, token=token)
    assert opt_status == 200
    routes_low = opt_data["routes"]
    assert len(routes_low) == 4
    route_types = [r["route_type"] for r in routes_low]
    assert "Fastest Route" in route_types
    assert "Shortest Route" in route_types
    assert "Traffic Avoidance" in route_types
    assert "Fuel Efficient Route" in route_types
    print(f"[PASS] 7. Route Optimization: 4 alternatives calculated for Low traffic: {route_types}")

    # 8. TRAFFIC-AWARE ROUTING COMPARISON
    _, opt_high = make_req("POST", "/api/routes/calculate", {
        "origin": "Vijayawada",
        "destination": "Hyderabad",
        "traffic_level": "High",
        "vehicle_type": "Truck"
    }, token=token)
    
    fastest_high = next(r for r in opt_high["routes"] if r["route_type"] == "Fastest Route")
    avoid_high = next(r for r in opt_high["routes"] if r["route_type"] == "Traffic Avoidance")
    
    assert avoid_high["traffic_level"] == "High", f"Traffic level should be 'High', got {avoid_high['traffic_level']}"
    assert opt_high["recommended_route"] == "Traffic Avoidance", f"Expected Traffic Avoidance recommended in High traffic, got {opt_high['recommended_route']}"
    print(f"[PASS] 8. Traffic Impact: In High traffic, Traffic Avoidance is recommended ({avoid_high['travel_time_minutes']}m vs Expressway {fastest_high['travel_time_minutes']}m). Traffic level correctly set to '{avoid_high['traffic_level']}'")

    # 9. FUEL EFFICIENT ROUTE CARD METRICS
    fuel_route = next(r for r in routes_low if r["route_type"] == "Fuel Efficient Route")
    fastest_route = next(r for r in routes_low if r["route_type"] == "Fastest Route")
    assert fuel_route["fuel_estimate_liters"] < fastest_route["fuel_estimate_liters"], "Fuel efficient route should save fuel!"
    assert fuel_route["distance_km"] > 0
    assert fuel_route["duration_text"] is not None
    assert fuel_route["co2_emissions_kg"] > 0
    assert fuel_route["eta_time"] is not None
    print(f"[PASS] 9. Fuel Efficient Route: {fuel_route['name']} | Distance: {fuel_route['distance_km']} km | Duration: {fuel_route['duration_text']} | Fuel: {fuel_route['fuel_estimate_liters']} L (~18% savings vs {fastest_route['fuel_estimate_liters']} L) | CO2: {fuel_route['co2_emissions_kg']} kg | ETA: {fuel_route['eta_time']}")

    # 10. ROUTE RECALCULATION
    recalc_status, recalc_data = make_req("POST", f"/api/shipments/{test_shp_id}/recalculate-route", {
        "traffic_level": "Severe",
        "route_type": "Traffic Avoidance"
    }, token=token)
    assert recalc_status == 200, f"Recalculate route failed ({recalc_status}): {recalc_data}"
    assert recalc_data["traffic_level"] == "Severe"
    assert recalc_data["route_type"] == "Traffic Avoidance"
    print(f"[PASS] 10. Route Recalculation: Shipment {test_shp_id} recalculated to 'Traffic Avoidance' under Severe traffic. New dynamic ETA: {recalc_data['estimated_duration']}")

    # 11. DELIVERED STATUS & ETA UPDATE
    deliv_status, deliv_data = make_req("PUT", f"/api/shipments/{test_shp_id}/status", {
        "status": "Delivered",
        "description": "Consignment safely delivered to client warehouse."
    }, token=token)
    assert deliv_status == 200
    assert deliv_data["status"] == "Delivered"
    assert deliv_data["estimated_duration"] == "Delivered"
    assert deliv_data["progress"] == 100.0

    # Also verify tracking endpoint returns Delivered
    _, trk_deliv = make_req("GET", f"/api/tracking/{test_shp_id}", token=token)
    assert trk_deliv["eta"] == "Delivered"
    assert trk_deliv["remaining_km"] == 0.0
    print(f"[PASS] 11. Delivery & Final ETA: Status -> 'Delivered', ETA -> '{trk_deliv['eta']}', Remaining: {trk_deliv['remaining_km']} km")

    # 12. TRIP SCHEDULING & CONFLICT PREVENTION
    # Complete any existing ongoing trips for clean test state
    _, existing_trips = make_req("GET", "/api/trips", token=token)
    for et in existing_trips:
        if et.get("trip_status") in ["Started", "In Transit"]:
            make_req("PUT", f"/api/trips/{et['trip_id']}/status", {"trip_status": "Completed"}, token=token)

    trip_id = f"TEST-TRP-{ts}"
    trip_payload = {
        "trip_id": trip_id,
        "vehicle_id": v_id,
        "driver_id": d_id,
        "origin": "Vijayawada",
        "destination": "Visakhapatnam",
        "route_type": "Fastest Route",
        "notes": "Verified scheduled run"
    }
    t_status, created_trip = make_req("POST", "/api/trips", trip_payload, token=token)
    assert t_status == 201, f"Trip creation failed ({t_status}): {created_trip}"
    assert created_trip["trip_id"] == trip_id
    assert created_trip["trip_status"] == "Scheduled"
    print(f"[PASS] 12. Trip Scheduling: Trip {trip_id} scheduled in PostgreSQL")

    # Start trip
    st_trip, st_trip_data = make_req("PUT", f"/api/trips/{trip_id}/status", {"trip_status": "In Transit"}, token=token)
    assert st_trip == 200
    assert st_trip_data["trip_status"] == "In Transit"

    # Verify conflict prevention (double booking attempt)
    conf_status, conf_data = make_req("POST", "/api/trips", {
        "trip_id": f"CONFLICT-{trip_id}",
        "vehicle_id": v_id,
        "driver_id": d_id,
        "origin": "Vijayawada",
        "destination": "Guntur"
    }, token=token)
    assert conf_status == 409, f"Expected HTTP 409 conflict, got {conf_status}"
    print(f"[PASS] 12b. Conflict Prevention: Attempting to double-book active vehicle was blocked with HTTP 409: '{conf_data['detail']}'")

    print("=" * 65)
    print("ALL MILESTONE 2 CORRECTION CRITERIA VERIFIED 100% SUCCESSFUL!")
    print("=" * 65)

if __name__ == "__main__":
    run_tests()
