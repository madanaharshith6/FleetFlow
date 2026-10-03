import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from ..auth import roles, current_user
from ..database import get_db
from ..models import Shipment, ShipmentHistory, Vehicle, Driver, User
from ..schemas import (
    ShipmentCreate,
    ShipmentResponse,
    ShipmentUpdate,
    ShipmentStatusUpdate,
    ShipmentAssign,
    ShipmentHistoryResponse,
    VALID_SHIPMENT_STATUSES
)
from ..services.route_optimizer import calculate_routes, geocode_city
from ..services.tracking_service import validate_status_transition, calculate_dynamic_eta
from ..services.websocket_manager import manager


router = APIRouter(
    prefix="/api/shipments",
    tags=["Shipment Tracking"]
)


def format_shipment_response(s: Shipment) -> dict:
    data = {
        "id": s.id,
        "shipment_id": s.shipment_id,
        "tracking_number": s.tracking_number,
        "customer_name": s.customer_name or "Acme Logistics",
        "customer_phone": s.customer_phone,
        "origin": s.origin,
        "destination": s.destination,
        "description": s.description,
        "status": s.status,
        "current_location": s.current_location,
        "due_date": s.due_date,
        "expected_delivery": s.expected_delivery,
        "scheduled_pickup": s.scheduled_pickup,
        "scheduled_delivery": s.scheduled_delivery,
        "actual_delivery": s.actual_delivery,
        "vehicle_id": s.vehicle_id,
        "driver_id": s.driver_id,
        "progress": s.progress or 0.0,
        "latitude": s.latitude,
        "longitude": s.longitude,
        "distance_km": s.distance_km or 0.0,
        "estimated_duration": s.estimated_duration or "TBD",
        "route_type": s.route_type or "Fastest Route",
        "traffic_level": s.traffic_level or "Moderate",
        "created_at": s.created_at,
        "updated_at": s.updated_at,
        "vehicle_info": None,
        "driver_info": None
    }
    if s.vehicle:
        data["vehicle_info"] = {
            "id": s.vehicle.id,
            "vehicle_id": s.vehicle.vehicle_id,
            "registration_number": s.vehicle.registration_number,
            "vehicle_type": s.vehicle.vehicle_type
        }
    if s.driver:
        data["driver_info"] = {
            "id": s.driver.id,
            "driver_id": s.driver.driver_id,
            "name": s.driver.name,
            "phone": s.driver.phone
        }
    return data


@router.get("", response_model=List[ShipmentResponse])
def get_shipments(
    db: Session = Depends(get_db),
    user: User = Depends(roles("Administrator", "Fleet Manager", "Dispatcher", "Driver")),
    search: Optional[str] = Query(None, description="Search tracking number, shipment id, customer, or route"),
    status: Optional[str] = Query(None, description="Filter by shipment status"),
    driver_id: Optional[int] = Query(None),
    vehicle_id: Optional[int] = Query(None)
):
    query = db.query(Shipment)

    # Search filter
    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Shipment.shipment_id.ilike(search_term),
                Shipment.tracking_number.ilike(search_term),
                Shipment.customer_name.ilike(search_term),
                Shipment.origin.ilike(search_term),
                Shipment.destination.ilike(search_term)
            )
        )

    # Status filter
    if status and status != "All":
        query = query.filter(Shipment.status == status)

    if driver_id:
        query = query.filter(Shipment.driver_id == driver_id)

    if vehicle_id:
        query = query.filter(Shipment.vehicle_id == vehicle_id)

    shipments = query.order_by(Shipment.id.desc()).all()
    return [format_shipment_response(s) for s in shipments]


@router.get("/{identifier}", response_model=ShipmentResponse)
def get_shipment(
    identifier: str,
    db: Session = Depends(get_db),
    user: User = Depends(roles("Administrator", "Fleet Manager", "Dispatcher", "Driver"))
):
    query = db.query(Shipment)
    if identifier.isdigit():
        shipment = query.filter(or_(Shipment.id == int(identifier), Shipment.shipment_id == identifier)).first()
    else:
        shipment = query.filter(or_(Shipment.shipment_id == identifier, Shipment.tracking_number == identifier)).first()

    if not shipment:
        raise HTTPException(status_code=404, detail=f"Shipment '{identifier}' not found")

    return format_shipment_response(shipment)


@router.post("", response_model=ShipmentResponse, status_code=status.HTTP_201_CREATED)
async def create_shipment(
    data: ShipmentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(roles("Administrator", "Fleet Manager", "Dispatcher"))
):
    clean_origin = data.origin.strip()
    clean_destination = data.destination.strip()

    # Generate IDs if not provided
    shipment_code = data.shipment_id.strip() if data.shipment_id else f"SHP-{uuid.uuid4().hex[:6].upper()}"
    tracking_code = data.tracking_number.strip() if data.tracking_number else f"TRK-{uuid.uuid4().hex[:8].upper()}"

    # Verify uniqueness
    if db.query(Shipment).filter(Shipment.shipment_id == shipment_code).first():
        raise HTTPException(status_code=409, detail="Shipment ID already exists")
    if db.query(Shipment).filter(Shipment.tracking_number == tracking_code).first():
        raise HTTPException(status_code=409, detail="Tracking number already exists")

    # Validate vehicle and driver if provided
    if data.vehicle_id and not db.query(Vehicle).filter(Vehicle.id == data.vehicle_id).first():
        raise HTTPException(status_code=404, detail="Assigned vehicle not found")
    if data.driver_id and not db.query(Driver).filter(Driver.id == data.driver_id).first():
        raise HTTPException(status_code=404, detail="Assigned driver not found")

    # Calculate realistic road metrics
    route_calc = calculate_routes(clean_origin, clean_destination, data.traffic_level or "Moderate")
    selected_route = next((r for r in route_calc["routes"] if r["route_type"] == (data.route_type or "Fastest Route")), route_calc["routes"][0])
    orig_coords = geocode_city(clean_origin)

    initial_status = "Assigned" if (data.vehicle_id or data.driver_id) else "Created"

    shipment = Shipment(
        shipment_id=shipment_code,
        tracking_number=tracking_code,
        customer_name=data.customer_name.strip(),
        customer_phone=data.customer_phone.strip() if data.customer_phone else None,
        origin=clean_origin,
        destination=clean_destination,
        description=data.description.strip() if data.description else f"Cargo transit from {clean_origin} to {clean_destination}",
        status=initial_status,
        current_location=f"{clean_origin} Logistics Hub",
        latitude=orig_coords[0],
        longitude=orig_coords[1],
        progress=0.0,
        distance_km=selected_route["distance_km"],
        estimated_duration=selected_route["duration_text"],
        route_type=selected_route["route_type"],
        traffic_level=data.traffic_level or "Moderate",
        scheduled_pickup=data.scheduled_pickup,
        scheduled_delivery=data.scheduled_delivery,
        vehicle_id=data.vehicle_id,
        driver_id=data.driver_id
    )

    # Initial ETA
    eta_dt, _, _ = calculate_dynamic_eta(0.0, shipment.distance_km, shipment.traffic_level, initial_status)
    shipment.expected_delivery = eta_dt

    db.add(shipment)
    db.commit()
    db.refresh(shipment)

    # Record history
    history = ShipmentHistory(
        shipment_id=shipment.id,
        event_type="Shipment Created",
        previous_status=None,
        new_status=initial_status,
        status=initial_status,
        current_location=shipment.current_location,
        progress=0.0,
        latitude=shipment.latitude,
        longitude=shipment.longitude,
        expected_delivery=shipment.expected_delivery,
        description=f"Shipment initialized. Tracking number: {tracking_code}. Route: {selected_route['name']}."
    )
    db.add(history)
    db.commit()

    # Broadcast event
    await manager.broadcast_to_shipment(shipment.shipment_id, {
        "type": "shipment_created",
        "shipment_id": shipment.shipment_id,
        "tracking_number": shipment.tracking_number,
        "status": shipment.status,
        "origin": shipment.origin,
        "destination": shipment.destination
    })

    return format_shipment_response(shipment)


@router.put("/{identifier}", response_model=ShipmentResponse)
def update_shipment(
    identifier: str,
    data: ShipmentUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(roles("Administrator", "Fleet Manager", "Dispatcher"))
):
    shipment = db.query(Shipment).filter(or_(Shipment.id == int(identifier) if identifier.isdigit() else False, Shipment.shipment_id == identifier)).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    update_fields = data.model_dump(exclude_unset=True)
    for field, val in update_fields.items():
        if val is not None:
            setattr(shipment, field, val.strip() if isinstance(val, str) else val)

    shipment.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(shipment)
    return format_shipment_response(shipment)


@router.put("/{identifier}/status", response_model=ShipmentResponse)
async def update_shipment_status(
    identifier: str,
    data: ShipmentStatusUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(roles("Administrator", "Fleet Manager", "Dispatcher", "Driver"))
):
    shipment = db.query(Shipment).filter(or_(Shipment.id == int(identifier) if identifier.isdigit() else False, Shipment.shipment_id == identifier)).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    target_status = data.status.strip()
    if target_status not in VALID_SHIPMENT_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status '{target_status}'. Must be one of: {VALID_SHIPMENT_STATUSES}")

    valid, err_msg = validate_status_transition(shipment.status, target_status)
    if not valid:
        raise HTTPException(status_code=400, detail=err_msg)

    prev_status = shipment.status
    shipment.status = target_status
    if data.location_name:
        shipment.current_location = data.location_name.strip()
    if data.latitude is not None:
        shipment.latitude = data.latitude
    if data.longitude is not None:
        shipment.longitude = data.longitude
    if data.progress is not None:
        shipment.progress = min(max(data.progress, 0.0), 100.0)

    if target_status == "Delivered":
        shipment.progress = 100.0
        shipment.actual_delivery = datetime.utcnow()
        if shipment.vehicle:
            shipment.vehicle.current_status = "Available"
    elif target_status == "In Transit":
        if shipment.vehicle:
            shipment.vehicle.current_status = "Active"

    # Recompute ETA
    eta_dt, dur_text, _ = calculate_dynamic_eta(shipment.progress, shipment.distance_km, shipment.traffic_level, target_status)
    shipment.expected_delivery = eta_dt
    shipment.estimated_duration = dur_text
    shipment.updated_at = datetime.utcnow()

    # Log into history
    history = ShipmentHistory(
        shipment_id=shipment.id,
        event_type="Status Changed",
        previous_status=prev_status,
        new_status=target_status,
        status=target_status,
        current_location=shipment.current_location,
        progress=shipment.progress,
        latitude=shipment.latitude,
        longitude=shipment.longitude,
        expected_delivery=shipment.expected_delivery,
        description=data.description or f"Shipment status transitioned from {prev_status} to {target_status} by {user.role}."
    )
    db.add(history)
    db.commit()
    db.refresh(shipment)

    # Broadcast via WebSocket
    await manager.broadcast_to_shipment(shipment.shipment_id, {
        "type": "status_changed",
        "shipment_id": shipment.shipment_id,
        "previous_status": prev_status,
        "status": target_status,
        "progress": shipment.progress,
        "current_location": shipment.current_location,
        "eta": dur_text
    })

    return format_shipment_response(shipment)


@router.post("/{identifier}/assign", response_model=ShipmentResponse)
async def assign_shipment_assets(
    identifier: str,
    data: ShipmentAssign,
    db: Session = Depends(get_db),
    user: User = Depends(roles("Administrator", "Fleet Manager", "Dispatcher"))
):
    shipment = db.query(Shipment).filter(or_(Shipment.id == int(identifier) if identifier.isdigit() else False, Shipment.shipment_id == identifier)).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    vehicle_obj = None
    driver_obj = None
    if data.vehicle_id:
        vehicle_obj = db.query(Vehicle).filter(Vehicle.id == data.vehicle_id).first()
        if not vehicle_obj:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        shipment.vehicle_id = data.vehicle_id

    if data.driver_id:
        driver_obj = db.query(Driver).filter(Driver.id == data.driver_id).first()
        if not driver_obj:
            raise HTTPException(status_code=404, detail="Driver not found")
        shipment.driver_id = data.driver_id

    prev_status = shipment.status
    if shipment.status == "Created" and (data.vehicle_id or data.driver_id):
        shipment.status = "Assigned"

    shipment.updated_at = datetime.utcnow()

    # Log into history
    history = ShipmentHistory(
        shipment_id=shipment.id,
        event_type="Asset Assigned",
        previous_status=prev_status,
        new_status=shipment.status,
        status=shipment.status,
        current_location=shipment.current_location,
        progress=shipment.progress,
        latitude=shipment.latitude,
        longitude=shipment.longitude,
        expected_delivery=shipment.expected_delivery,
        description=f"Assigned Vehicle: {vehicle_obj.vehicle_id if vehicle_obj else 'None'}, Driver: {driver_obj.name if driver_obj else 'None'}."
    )
    db.add(history)
    db.commit()
    db.refresh(shipment)

    # Broadcast via WebSocket
    await manager.broadcast_to_shipment(shipment.shipment_id, {
        "type": "asset_assigned",
        "shipment_id": shipment.shipment_id,
        "vehicle_id": shipment.vehicle_id,
        "driver_id": shipment.driver_id,
        "status": shipment.status
    })

    return format_shipment_response(shipment)


@router.get("/{identifier}/history", response_model=List[ShipmentHistoryResponse])
def get_shipment_history(
    identifier: str,
    db: Session = Depends(get_db),
    user: User = Depends(roles("Administrator", "Fleet Manager", "Dispatcher", "Driver"))
):
    shipment = db.query(Shipment).filter(or_(Shipment.id == int(identifier) if identifier.isdigit() else False, Shipment.shipment_id == identifier)).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    return db.query(ShipmentHistory).filter(ShipmentHistory.shipment_id == shipment.id).order_by(ShipmentHistory.created_at.desc()).all()


@router.delete("/{identifier}", status_code=status.HTTP_200_OK)
def delete_shipment(
    identifier: str,
    db: Session = Depends(get_db),
    user: User = Depends(roles("Administrator", "Fleet Manager"))
):
    shipment = db.query(Shipment).filter(or_(Shipment.id == int(identifier) if identifier.isdigit() else False, Shipment.shipment_id == identifier)).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    db.delete(shipment)
    db.commit()
    return {"message": f"Shipment '{identifier}' deleted successfully"}