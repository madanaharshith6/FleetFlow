from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_

from ..auth import roles
from ..database import get_db
from ..models import Shipment, ShipmentHistory, User
from ..schemas import LocationUpdate, TrackingTelemetryResponse
from ..services.tracking_service import simulate_gps_progress_step, calculate_dynamic_eta
from ..services.websocket_manager import manager


router = APIRouter(
    prefix="/api/tracking",
    tags=["GPS & Live Tracking"]
)


@router.get("/{identifier}", response_model=TrackingTelemetryResponse)
def get_live_tracking_telemetry(
    identifier: str,
    db: Session = Depends(get_db),
    user: User = Depends(roles("Administrator", "Fleet Manager", "Dispatcher", "Driver"))
):
    shipment = db.query(Shipment).filter(or_(Shipment.id == int(identifier) if identifier.isdigit() else False, Shipment.shipment_id == identifier, Shipment.tracking_number == identifier)).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    eta_dt, dur_text, rem_km = calculate_dynamic_eta(
        shipment.progress or 0.0,
        shipment.distance_km or 250.0,
        shipment.traffic_level or "Moderate",
        shipment.status
    )

    gps_status = "Simulated GPS: Active Corridor"
    if shipment.status == "Delivered":
        gps_status = "Simulated GPS: Arrived / Completed"
    elif shipment.status == "Cancelled":
        gps_status = "Simulated GPS: Cancelled"
    elif not shipment.latitude or not shipment.longitude:
        gps_status = "Simulated GPS: Awaiting Waypoint"

    vehicle_info = None
    if shipment.vehicle:
        vehicle_info = {
            "vehicle_id": shipment.vehicle.vehicle_id,
            "registration": shipment.vehicle.registration_number,
            "type": shipment.vehicle.vehicle_type
        }

    driver_info = None
    if shipment.driver:
        driver_info = {
            "driver_id": shipment.driver.driver_id,
            "name": shipment.driver.name,
            "phone": shipment.driver.phone
        }

    return {
        "shipment_id": shipment.shipment_id,
        "tracking_number": shipment.tracking_number,
        "status": shipment.status,
        "origin": shipment.origin,
        "destination": shipment.destination,
        "current_location": shipment.current_location,
        "latitude": shipment.latitude,
        "longitude": shipment.longitude,
        "progress": shipment.progress or 0.0,
        "distance_km": shipment.distance_km or 0.0,
        "remaining_km": rem_km,
        "estimated_duration": dur_text,
        "eta": "Delivered" if shipment.status == "Delivered" else ("Cancelled" if shipment.status == "Cancelled" else (eta_dt.strftime("%Y-%m-%d %H:%M UTC") if eta_dt else dur_text)),
        "traffic_level": shipment.traffic_level or "Moderate",
        "gps_status": gps_status,
        "last_update": shipment.updated_at or datetime.utcnow(),
        "vehicle_info": vehicle_info,
        "driver_info": driver_info
    }


@router.post("/{identifier}/location")
async def record_gps_location(
    identifier: str,
    data: LocationUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(roles("Administrator", "Fleet Manager", "Dispatcher", "Driver"))
):
    shipment = db.query(Shipment).filter(or_(Shipment.id == int(identifier) if identifier.isdigit() else False, Shipment.shipment_id == identifier)).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    shipment.latitude = round(data.latitude, 4)
    shipment.longitude = round(data.longitude, 4)
    if data.location_name:
        shipment.current_location = data.location_name.strip()
    if data.progress is not None:
        shipment.progress = min(max(data.progress, 0.0), 100.0)

    shipment.updated_at = datetime.utcnow()

    # Log into history
    history = ShipmentHistory(
        shipment_id=shipment.id,
        event_type="GPS Coordinate Logged",
        previous_status=shipment.status,
        new_status=shipment.status,
        status=shipment.status,
        current_location=shipment.current_location,
        progress=shipment.progress,
        latitude=shipment.latitude,
        longitude=shipment.longitude,
        expected_delivery=shipment.expected_delivery,
        description=f"GPS telemetry updated to ({shipment.latitude}, {shipment.longitude}). Speed: {data.speed_kmh} km/h."
    )
    db.add(history)
    db.commit()

    # Broadcast via WebSocket
    payload = {
        "type": "location_updated",
        "shipment_id": shipment.shipment_id,
        "latitude": shipment.latitude,
        "longitude": shipment.longitude,
        "location_name": shipment.current_location,
        "progress": shipment.progress,
        "timestamp": shipment.updated_at.isoformat()
    }
    await manager.broadcast_to_shipment(shipment.shipment_id, payload)

    return {"message": "Location updated successfully", "telemetry": payload}


@router.post("/{identifier}/simulate-step")
async def simulate_gps_progress(
    identifier: str,
    db: Session = Depends(get_db),
    user: User = Depends(roles("Administrator", "Fleet Manager", "Dispatcher", "Driver"))
):
    """
    Simulation endpoint for live mentor presentation:
    Advances the vehicle along the transit corridor by a realistic interval.
    """
    shipment = db.query(Shipment).filter(or_(Shipment.id == int(identifier) if identifier.isdigit() else False, Shipment.shipment_id == identifier)).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    result = simulate_gps_progress_step(db, shipment, step_increment_percent=15.0)

    # Broadcast step via WebSocket
    await manager.broadcast_to_shipment(shipment.shipment_id, {
        "type": "location_updated",
        **result
    })

    return result
