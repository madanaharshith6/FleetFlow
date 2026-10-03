import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from ..auth import roles
from ..database import get_db
from ..models import Trip, Vehicle, Driver, Shipment, User
from ..schemas import TripCreate, TripResponse, TripStatusUpdate, VALID_TRIP_STATUSES
from ..services.route_optimizer import calculate_routes


router = APIRouter(
    prefix="/api/trips",
    tags=["Trip Scheduling"]
)


def format_trip_response(t: Trip) -> dict:
    return {
        "id": t.id,
        "trip_id": t.trip_id,
        "shipment_id": t.shipment_id,
        "vehicle_id": t.vehicle_id,
        "driver_id": t.driver_id,
        "origin": t.origin,
        "destination": t.destination,
        "trip_status": t.trip_status,
        "route_type": t.route_type,
        "distance_km": t.distance_km,
        "scheduled_start": t.scheduled_start,
        "scheduled_arrival": t.scheduled_arrival,
        "actual_start": t.actual_start,
        "actual_arrival": t.actual_arrival,
        "notes": t.notes,
        "created_at": t.created_at,
        "vehicle_code": t.vehicle.vehicle_id if t.vehicle else None,
        "driver_name": t.driver.name if t.driver else None,
        "shipment_code": t.shipment.shipment_id if t.shipment else None
    }


@router.get("", response_model=List[TripResponse])
def list_trips(
    db: Session = Depends(get_db),
    user: User = Depends(roles("Administrator", "Fleet Manager", "Dispatcher", "Driver")),
    status: Optional[str] = Query(None),
    vehicle_id: Optional[int] = Query(None),
    driver_id: Optional[int] = Query(None)
):
    query = db.query(Trip)
    if status and status != "All":
        query = query.filter(Trip.trip_status == status)
    if vehicle_id:
        query = query.filter(Trip.vehicle_id == vehicle_id)
    if driver_id:
        query = query.filter(Trip.driver_id == driver_id)

    trips = query.order_by(Trip.id.desc()).all()
    return [format_trip_response(t) for t in trips]


@router.post("", response_model=TripResponse, status_code=status.HTTP_201_CREATED)
def create_trip(
    data: TripCreate,
    db: Session = Depends(get_db),
    user: User = Depends(roles("Administrator", "Fleet Manager", "Dispatcher"))
):
    # Verify vehicle and driver exist
    vehicle = db.query(Vehicle).filter(Vehicle.id == data.vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    driver = db.query(Driver).filter(Driver.id == data.driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    # Conflict check: ensure vehicle and driver are not in an active overlapping trip
    active_vehicle_trip = db.query(Trip).filter(
        Trip.vehicle_id == data.vehicle_id,
        Trip.trip_status.in_(["Started", "In Transit"])
    ).first()
    if active_vehicle_trip:
        raise HTTPException(
            status_code=409,
            detail=f"Vehicle '{vehicle.vehicle_id}' is currently committed to ongoing Trip '{active_vehicle_trip.trip_id}'"
        )

    active_driver_trip = db.query(Trip).filter(
        Trip.driver_id == data.driver_id,
        Trip.trip_status.in_(["Started", "In Transit"])
    ).first()
    if active_driver_trip:
        raise HTTPException(
            status_code=409,
            detail=f"Driver '{driver.name}' is currently on ongoing Trip '{active_driver_trip.trip_id}'"
        )

    trip_code = data.trip_id.strip() if data.trip_id else f"TRP-{uuid.uuid4().hex[:6].upper()}"
    if db.query(Trip).filter(Trip.trip_id == trip_code).first():
        raise HTTPException(status_code=409, detail="Trip ID already exists")

    # Compute distance if not given
    dist = data.distance_km or 0.0
    if dist <= 0.0:
        route_info = calculate_routes(data.origin, data.destination)
        dist = route_info["routes"][0]["distance_km"]

    trip = Trip(
        trip_id=trip_code,
        shipment_id=data.shipment_id,
        vehicle_id=data.vehicle_id,
        driver_id=data.driver_id,
        origin=data.origin.strip(),
        destination=data.destination.strip(),
        trip_status="Scheduled",
        route_type=data.route_type or "Fastest Route",
        distance_km=dist,
        scheduled_start=data.scheduled_start,
        scheduled_arrival=data.scheduled_arrival,
        notes=data.notes
    )

    db.add(trip)
    db.commit()
    db.refresh(trip)
    return format_trip_response(trip)


@router.put("/{trip_id}/status", response_model=TripResponse)
def update_trip_status(
    trip_id: str,
    data: TripStatusUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(roles("Administrator", "Fleet Manager", "Dispatcher", "Driver"))
):
    trip = db.query(Trip).filter(or_(Trip.id == int(trip_id) if trip_id.isdigit() else False, Trip.trip_id == trip_id)).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    target_status = data.trip_status.strip()
    if target_status not in VALID_TRIP_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid trip status '{target_status}'. Must be one of: {VALID_TRIP_STATUSES}")

    trip.trip_status = target_status
    if data.notes:
        trip.notes = data.notes

    if target_status in ["Started", "In Transit"] and not trip.actual_start:
        trip.actual_start = datetime.utcnow()
        if trip.vehicle:
            trip.vehicle.current_status = "Active"
    elif target_status in ["Completed", "Cancelled"]:
        trip.actual_arrival = datetime.utcnow()
        if trip.vehicle:
            trip.vehicle.current_status = "Available"

    db.commit()
    db.refresh(trip)
    return format_trip_response(trip)
