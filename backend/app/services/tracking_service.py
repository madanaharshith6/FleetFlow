from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from ..models import Shipment, ShipmentHistory, Vehicle, Driver
from .route_optimizer import geocode_city, haversine_distance, TRAFFIC_MULTIPLIERS


VALID_TRANSITIONS = {
    "Created": ["Assigned", "In Transit", "Cancelled"],
    "Assigned": ["In Transit", "Delayed", "Created", "Cancelled"],
    "In Transit": ["Delayed", "Delivered", "Cancelled"],
    "Delayed": ["In Transit", "Delivered", "Cancelled"],
    "Delivered": [],
    "Cancelled": []
}


def validate_status_transition(current_status: str, target_status: str) -> Tuple[bool, str]:
    """Ensure logical status progression according to logistics workflows."""
    if current_status == target_status:
        return True, ""
    
    allowed = VALID_TRANSITIONS.get(current_status, [])
    if target_status not in allowed:
        return False, f"Cannot transition shipment from '{current_status}' to '{target_status}'. Allowed transitions: {allowed}"
    
    return True, ""


def calculate_dynamic_eta(
    progress: float,
    total_distance_km: float,
    traffic_level: str = "Moderate",
    status: str = "In Transit"
) -> Tuple[Optional[datetime], str, float]:
    """
    Calculate real-time ETA, remaining distance, and duration text based on current position and traffic.
    """
    if status == "Delivered":
        return None, "Delivered", 0.0
    if status == "Cancelled":
        return None, "Cancelled", 0.0

    remaining_km = max(round(total_distance_km * (1.0 - (progress / 100.0)), 1), 0.0)
    if remaining_km == 0:
        return None, "Arrived at destination", 0.0

    traffic_factor = TRAFFIC_MULTIPLIERS.get(traffic_level, 1.18)
    avg_speed_kmh = 55.0
    travel_time_hours = (remaining_km / avg_speed_kmh) * traffic_factor
    travel_time_minutes = max(int(round(travel_time_hours * 60)), 5)

    now = datetime.utcnow()
    eta_datetime = now + timedelta(minutes=travel_time_minutes)

    if travel_time_minutes >= 60:
        hrs = travel_time_minutes // 60
        mins = travel_time_minutes % 60
        duration_text = f"{hrs}h {mins}m"
    else:
        duration_text = f"{travel_time_minutes} mins"

    return eta_datetime, duration_text, remaining_km


def simulate_gps_progress_step(
    db: Session,
    shipment: Shipment,
    step_increment_percent: float = 15.0
) -> Dict[str, Any]:
    """
    Simulate the vehicle moving forward along its assigned route.
    Calculates intermediate coordinates, logs history, and updates ETA.
    """
    start_coords = geocode_city(shipment.origin)
    end_coords = geocode_city(shipment.destination)

    old_progress = shipment.progress or 0.0
    new_progress = min(round(old_progress + step_increment_percent, 1), 100.0)

    # Linear interpolation between origin and destination coordinates
    ratio = new_progress / 100.0
    curr_lat = round(start_coords[0] + ratio * (end_coords[0] - start_coords[0]), 4)
    curr_lon = round(start_coords[1] + ratio * (end_coords[1] - start_coords[1]), 4)

    # Location description
    if new_progress >= 100.0:
        loc_name = f"{shipment.destination} Logistic Hub"
        new_status = "Delivered"
    elif new_progress >= 75.0:
        loc_name = f"Approaching {shipment.destination} Outer Ring"
        new_status = shipment.status if shipment.status != "Created" else "In Transit"
    elif new_progress >= 50.0:
        loc_name = f"Midway Transit Corridor ({shipment.origin} - {shipment.destination})"
        new_status = "In Transit"
    elif new_progress >= 25.0:
        loc_name = f"NH Tollway Outbound from {shipment.origin}"
        new_status = "In Transit"
    else:
        loc_name = f"{shipment.origin} Dispatch Hub"
        new_status = shipment.status

    # Recalculate ETA
    eta_dt, duration_text, remaining_km = calculate_dynamic_eta(
        new_progress,
        shipment.distance_km or 250.0,
        shipment.traffic_level or "Moderate",
        new_status
    )

    prev_status = shipment.status
    shipment.latitude = curr_lat
    shipment.longitude = curr_lon
    shipment.current_location = loc_name
    shipment.progress = new_progress
    shipment.expected_delivery = eta_dt
    shipment.estimated_duration = duration_text
    shipment.updated_at = datetime.utcnow()

    # Update status if completed
    if new_progress >= 100.0 and prev_status != "Delivered":
        shipment.status = "Delivered"
        shipment.actual_delivery = datetime.utcnow()
        if shipment.vehicle:
            shipment.vehicle.current_status = "Available"
    elif shipment.status in ["Created", "Assigned"] and new_progress > 0:
        shipment.status = "In Transit"
        if shipment.vehicle:
            shipment.vehicle.current_status = "Active"

    # Log into ShipmentHistory
    history_entry = ShipmentHistory(
        shipment_id=shipment.id,
        event_type="GPS Telemetry Update",
        previous_status=prev_status,
        new_status=shipment.status,
        status=shipment.status,
        current_location=loc_name,
        progress=new_progress,
        latitude=curr_lat,
        longitude=curr_lon,
        expected_delivery=eta_dt,
        description=f"Simulated GPS position updated to {loc_name} ({new_progress}% progress, {remaining_km} km remaining)."
    )
    db.add(history_entry)
    db.commit()
    db.refresh(shipment)

    return {
        "shipment_id": shipment.shipment_id,
        "tracking_number": shipment.tracking_number,
        "status": shipment.status,
        "progress": new_progress,
        "latitude": curr_lat,
        "longitude": curr_lon,
        "location_name": loc_name,
        "remaining_km": remaining_km,
        "eta": duration_text,
        "gps_status": "Simulated GPS (Advancing)" if new_progress < 100 else "Simulated GPS (Arrived)",
        "timestamp": datetime.utcnow().isoformat()
    }
