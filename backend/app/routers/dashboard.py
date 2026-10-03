from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Vehicle, Driver, Shipment, Trip, User
from ..auth import roles

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/summary")
def summary(
    db: Session = Depends(get_db),
    user: User = Depends(roles("Administrator", "Fleet Manager", "Dispatcher", "Driver"))
):
    # Milestone 1 Fleet & Driver Metrics
    total_vehicles = db.query(Vehicle).count()
    active_vehicles = db.query(Vehicle).filter(Vehicle.current_status == "Active").count()
    available_vehicles = db.query(Vehicle).filter(Vehicle.current_status == "Available").count()
    maintenance_vehicles = db.query(Vehicle).filter(Vehicle.current_status == "Maintenance").count()
    active_drivers = db.query(Driver).filter(Driver.is_active == True).count()

    # Milestone 2 Shipment & Logistics Metrics
    total_shipments = db.query(Shipment).count()
    in_transit_shipments = db.query(Shipment).filter(Shipment.status == "In Transit").count()
    delayed_shipments = db.query(Shipment).filter(Shipment.status == "Delayed").count()
    delivered_shipments = db.query(Shipment).filter(Shipment.status == "Delivered").count()
    cancelled_shipments = db.query(Shipment).filter(Shipment.status == "Cancelled").count()
    active_shipments = db.query(Shipment).filter(Shipment.status.in_(["Created", "Assigned", "In Transit", "Delayed"])).count()
    active_trips = db.query(Trip).filter(Trip.trip_status.in_(["Started", "In Transit"])).count()

    # Top recent shipments for the live operational feed
    recent_shipments_query = db.query(Shipment).order_by(Shipment.id.desc()).limit(6).all()
    recent_shipments = []
    for s in recent_shipments_query:
        recent_shipments.append({
            "id": s.id,
            "shipment_id": s.shipment_id,
            "tracking_number": s.tracking_number,
            "origin": s.origin,
            "destination": s.destination,
            "status": s.status,
            "progress": s.progress or 0.0,
            "driver_name": s.driver.name if s.driver else "Unassigned",
            "vehicle_id": s.vehicle.vehicle_id if s.vehicle else "Unassigned",
            "eta": "Delivered" if s.status == "Delivered" else ("Cancelled" if s.status == "Cancelled" else (s.estimated_duration or "TBD"))
        })

    return {
        # Milestone 1
        "total_vehicles": total_vehicles,
        "active_vehicles": active_vehicles,
        "available_vehicles": available_vehicles,
        "maintenance_vehicles": maintenance_vehicles,
        "active_drivers": active_drivers,
        # Milestone 2
        "total_shipments": total_shipments,
        "active_shipments": active_shipments,
        "in_transit_shipments": in_transit_shipments,
        "delayed_shipments": delayed_shipments,
        "delivered_shipments": delivered_shipments,
        "cancelled_shipments": cancelled_shipments,
        "active_trips": active_trips,
        "recent_shipments": recent_shipments
    }
