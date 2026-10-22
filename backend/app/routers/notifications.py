from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import MaintenanceRecord, Shipment, Driver, Vehicle, User
from ..auth import current_user
from ..schemas import NotificationItemResponse

router = APIRouter(prefix="/api/notifications", tags=["Notification Module"])


@router.get("", response_model=List[NotificationItemResponse])
def get_notifications(
    db: Session = Depends(get_db),
    user: User = Depends(current_user)
):
    """
    Module 8: Notification Module
    Aggregates real database-backed operational alerts:
    - Maintenance alerts (Overdue, Due Soon within 48h, Urgent Priority)
    - Delivery notifications (In-Transit, Delivered, Delayed)
    - Driver assignment alerts
    - Route traffic alerts
    """
    now = datetime.utcnow()
    in_48h = now + timedelta(hours=48)
    notifications = []

    # 1. Maintenance Alerts
    maint_records = db.query(MaintenanceRecord).all()
    for m in maint_records:
        veh_code = m.vehicle.vehicle_id if m.vehicle else f"Vehicle #{m.vehicle_id}"
        if m.status in ["Scheduled", "In Progress"] and m.scheduled_date and m.scheduled_date < now:
            notifications.append({
                "id": f"notif-maint-overdue-{m.id}",
                "category": "Maintenance",
                "title": f"Overdue Service: {veh_code}",
                "message": f"{m.category} was scheduled for {m.scheduled_date.strftime('%Y-%m-%d')} and is now overdue.",
                "severity": "critical",
                "timestamp": m.scheduled_date.isoformat()
            })
        elif m.status == "Scheduled" and m.scheduled_date and now <= m.scheduled_date <= in_48h:
            notifications.append({
                "id": f"notif-maint-duesoon-{m.id}",
                "category": "Maintenance",
                "title": f"Service Due Soon: {veh_code}",
                "message": f"{m.category} scheduled within 48h ({m.scheduled_date.strftime('%Y-%m-%d %H:%M')}).",
                "severity": "warning",
                "timestamp": m.scheduled_date.isoformat()
            })
        elif m.priority in ["High", "Urgent"] and m.status in ["Scheduled", "In Progress"]:
            notifications.append({
                "id": f"notif-maint-priority-{m.id}",
                "category": "Maintenance",
                "title": f"{m.priority} Priority Service: {veh_code}",
                "message": f"{m.category} requires urgent maintenance center staging.",
                "severity": "warning",
                "timestamp": m.created_at.isoformat() if m.created_at else now.isoformat()
            })

    # 2. Shipment & Delivery Notifications
    shipments = db.query(Shipment).all()
    for s in shipments:
        if s.status == "In Transit":
            notifications.append({
                "id": f"notif-ship-transit-{s.id}",
                "category": "Delivery",
                "title": f"Shipment In Transit: {s.tracking_number}",
                "message": f"Consignment en route from {s.origin} to {s.destination} ({s.progress:.0f}% completed).",
                "severity": "info",
                "timestamp": s.updated_at.isoformat() if s.updated_at else now.isoformat()
            })
        elif s.status == "Delayed":
            notifications.append({
                "id": f"notif-ship-delayed-{s.id}",
                "category": "Delivery",
                "title": f"Delivery Delayed: {s.tracking_number}",
                "message": f"Shipment from {s.origin} to {s.destination} experienced transit delay.",
                "severity": "warning",
                "timestamp": s.updated_at.isoformat() if s.updated_at else now.isoformat()
            })
        elif s.status == "Delivered":
            notifications.append({
                "id": f"notif-ship-delivered-{s.id}",
                "category": "Delivery",
                "title": f"Delivery Fulfilled: {s.tracking_number}",
                "message": f"Consignment successfully delivered to {s.destination}.",
                "severity": "info",
                "timestamp": s.actual_delivery.isoformat() if s.actual_delivery else (s.updated_at.isoformat() if s.updated_at else now.isoformat())
            })
        
        # Route traffic alert
        if s.traffic_level in ["High", "Severe"] and s.status in ["Assigned", "In Transit"]:
            notifications.append({
                "id": f"notif-traffic-{s.id}",
                "category": "Route Alert",
                "title": f"{s.traffic_level} Traffic Congestion: {s.tracking_number}",
                "message": f"Route on corridor {s.origin} → {s.destination} experiencing {s.traffic_level} congestion.",
                "severity": "warning",
                "timestamp": s.updated_at.isoformat() if s.updated_at else now.isoformat()
            })

    # 3. Driver Assignment Notifications
    drivers = db.query(Driver).all()
    for d in drivers:
        if d.vehicles and len(d.vehicles) > 0:
            veh = d.vehicles[0]
            notifications.append({
                "id": f"notif-driver-assigned-{d.id}",
                "category": "Driver Assignment",
                "title": f"Driver On Duty: {d.name}",
                "message": f"Assigned to commercial asset {veh.vehicle_id} ({veh.registration_number}).",
                "severity": "info",
                "timestamp": d.created_at.isoformat() if d.created_at else now.isoformat()
            })

    # Sort notifications reverse chronologically
    notifications.sort(key=lambda x: x["timestamp"], reverse=True)
    return notifications[:25]
