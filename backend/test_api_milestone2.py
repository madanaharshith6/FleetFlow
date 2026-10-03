import urllib.request
import json

def post(url, data, token=None):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    req = urllib.request.Request(url, data=json.dumps(data).encode(), headers=headers)
    return json.loads(urllib.request.urlopen(req).read().decode())

def get(url, token=None):
    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    req = urllib.request.Request(url, headers=headers)
    return json.loads(urllib.request.urlopen(req).read().decode())

def main():
    print("========================================")
    print("FLEETFLOW MILESTONE 2 API VERIFICATION")
    print("========================================")

    # 1. Login
    auth = post('http://127.0.0.1:8000/api/auth/login', {'email': 'admin@fleetflow.com', 'password': 'Admin@123'})
    token = auth['access_token']
    print(f"1. Login OK. Role: {auth['role']}")

    # 2. Route Calculation
    routes = post('http://127.0.0.1:8000/api/routes/calculate', {
        'origin': 'Vijayawada',
        'destination': 'Hyderabad',
        'traffic_level': 'Moderate'
    }, token)
    print(f"2. Routes calculated: {len(routes['routes'])}, Recommended: {routes['recommended_route']}")
    for r in routes['routes']:
        print(f"   * {r['route_type']}: {r['distance_km']} km | {r['duration_text']} | ETA: {r['eta_time']}")

    # 3. Shipments List
    shipments = get('http://127.0.0.1:8000/api/shipments', token)
    print(f"3. Existing Shipments Count: {len(shipments)}")

    # 4. Create New Shipment
    new_shp = post('http://127.0.0.1:8000/api/shipments', {
        'origin': 'Guntur',
        'destination': 'Visakhapatnam',
        'customer_name': 'Vizag Steel Industries',
        'route_type': 'Fastest Route',
        'traffic_level': 'Moderate'
    }, token)
    sid = new_shp['shipment_id']
    trk = new_shp['tracking_number']
    print(f"4. Created Shipment: {sid} (Tracking: {trk}) - {new_shp['distance_km']} km, ETA: {new_shp['estimated_duration']}")

    # 5. Assign Asset
    assigned = post(f'http://127.0.0.1:8000/api/shipments/{sid}/assign', {
        'vehicle_id': 1,
        'driver_id': 1
    }, token)
    print(f"5. Asset Assignment: Status={assigned['status']}, Driver={assigned['driver_info']['name']}, Vehicle={assigned['vehicle_info']['vehicle_id']}")

    # 6. Simulate GPS Progress
    sim = post(f'http://127.0.0.1:8000/api/tracking/{sid}/simulate-step', {}, token)
    print(f"6. GPS Telemetry Step: Progress={sim['progress']}%, Status={sim['status']}, Location={sim['location_name']}, Remaining={sim['remaining_km']} km")

    # 7. Query Telemetry
    telem = get(f'http://127.0.0.1:8000/api/tracking/{sid}', token)
    print(f"7. Live Telemetry: GPS Status={telem['gps_status']}, Lat/Lng=({telem['latitude']}, {telem['longitude']}), ETA={telem['eta']}")

    # 8. Query History
    hist = get(f'http://127.0.0.1:8000/api/shipments/{sid}/history', token)
    print(f"8. Audit History Log: {len(hist)} events recorded")
    for h in hist[:3]:
        print(f"   * [{h['created_at']}] {h['event_type']}: {h['description']}")

    # 9. Test Trip Scheduling
    trips = post('http://127.0.0.1:8000/api/trips', {
        'shipment_id': new_shp['id'],
        'vehicle_id': 2,
        'driver_id': 1,
        'origin': 'Vijayawada',
        'destination': 'Hyderabad',
        'route_type': 'Fastest Route',
        'notes': 'Express transit schedule'
    }, token)
    print(f"9. Trip Scheduled: {trips['trip_id']} - Status: {trips['trip_status']}, Driver: {trips['driver_name']}")

    # 10. Dashboard Summary
    dash = get('http://127.0.0.1:8000/api/dashboard/summary', token)
    print("10. Dashboard Extended Summary:")
    print(f"    - Vehicles: Total={dash['total_vehicles']}, Active={dash['active_vehicles']}, Available={dash['available_vehicles']}")
    print(f"    - Drivers: Active={dash['active_drivers']}")
    print(f"    - Shipments: Total={dash['total_shipments']}, Active={dash['active_shipments']}, In Transit={dash['in_transit_shipments']}, Delivered={dash['delivered_shipments']}")
    print(f"    - Trips: Active={dash['active_trips']}")
    print(f"    - Recent Feed Items: {len(dash['recent_shipments'])}")
    print("========================================")
    print("ALL BACKEND ENDPOINTS PASSED WITH 100% SUCCESS!")
    print("========================================")

if __name__ == '__main__':
    main()
