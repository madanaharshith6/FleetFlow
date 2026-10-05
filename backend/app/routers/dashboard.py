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

    # Milestone 3 Maintenance & Fleet Analytics Metrics
    from datetime import datetime
    from ..models import MaintenanceRecord
    from ..services.route_optimizer import FUEL_CONSUMPTION_KM_PER_LITER

    now = datetime.utcnow()
    all_maintenance = db.query(MaintenanceRecord).all()
    total_maint = len(all_maintenance)
    sched_maint = sum(1 for m in all_maintenance if m.status == "Scheduled" and m.scheduled_date >= now)
    in_prog_maint = sum(1 for m in all_maintenance if m.status == "In Progress")
    comp_maint = sum(1 for m in all_maintenance if m.status == "Completed")
    overdue_maint = sum(1 for m in all_maintenance if m.status == "Overdue" or (m.status in ["Scheduled", "In Progress"] and m.scheduled_date < now))
    total_maint_cost = round(sum(m.cost for m in all_maintenance if m.cost), 2)

    utilization_pct = round((active_vehicles / total_vehicles * 100), 1) if total_vehicles > 0 else 0.0

    # Fuel consumption estimate across trips
    trips = db.query(Trip).all()
    total_fuel_liters = 0.0
    for t in trips:
        eff = 4.5
        if t.vehicle:
            eff = FUEL_CONSUMPTION_KM_PER_LITER.get(t.vehicle.vehicle_type, 4.5)
        dist = t.distance_km or 0.0
        total_fuel_liters += (dist / eff)
    total_fuel_liters = round(total_fuel_liters, 1)

    # Active alerts
    alerts_query = db.query(MaintenanceRecord).filter(
        MaintenanceRecord.status.in_(["Scheduled", "In Progress", "Overdue"])
    ).order_by(MaintenanceRecord.scheduled_date.asc()).limit(4).all()
    active_alerts = []
    for m in alerts_query:
        is_over = m.status == "Overdue" or m.scheduled_date < now
        active_alerts.append({
            "id": m.id,
            "maintenance_id": m.maintenance_id,
            "vehicle_code": m.vehicle.vehicle_id if m.vehicle else "N/A",
            "category": m.category,
            "scheduled_date": m.scheduled_date.strftime("%Y-%m-%d"),
            "status": "Overdue" if is_over else m.status,
            "priority": m.priority,
            "severity": "critical" if (is_over or m.priority == "Urgent") else ("warning" if m.priority == "High" else "info")
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
        "recent_shipments": recent_shipments,
        # Milestone 3
        "total_maintenance": total_maint,
        "scheduled_maintenance": sched_maint,
        "in_progress_maintenance": in_prog_maint,
        "completed_maintenance": comp_maint,
        "overdue_maintenance": overdue_maint,
        "total_maintenance_cost": total_maint_cost,
        "fleet_utilization_percent": utilization_pct,
        "total_fuel_consumed_liters": total_fuel_liters,
        "recent_alerts": active_alerts
    }
