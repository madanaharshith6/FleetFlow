import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc

from ..auth import roles
from ..database import get_db
from ..models import MaintenanceRecord, MaintenanceHistory, Vehicle, User
from ..schemas import (
    MaintenanceCreate,
    MaintenanceUpdate,
    MaintenanceStatusUpdate,
    MaintenanceResponse,
    MaintenanceHistoryResponse,
    MaintenanceAlertResponse,
    MaintenanceSummaryResponse,
    VALID_MAINTENANCE_CATEGORIES,
    VALID_MAINTENANCE_STATUSES,
    VALID_MAINTENANCE_PRIORITIES
)

router = APIRouter(prefix="/api/maintenance", tags=["Vehicle Maintenance Management"])


def ensure_naive_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def format_maintenance(m: MaintenanceRecord) -> dict:
    now = datetime.utcnow()
    m_sched = ensure_naive_utc(m.scheduled_date)
    is_overdue = (m.status in ["Scheduled", "In Progress"] and m_sched and m_sched < now) or m.status == "Overdue"
    days_until_due = (m_sched.date() - now.date()).days if m_sched else 0

    return {
        "id": m.id,
        "maintenance_id": m.maintenance_id,
        "vehicle_id": m.vehicle_id,
        "vehicle_code": m.vehicle.vehicle_id if m.vehicle else None,
        "registration_number": m.vehicle.registration_number if m.vehicle else None,
        "vehicle_type": m.vehicle.vehicle_type if m.vehicle else None,
        "category": m.category,
        "description": m.description,
        "scheduled_date": m.scheduled_date,
        "service_date": m.service_date,
        "status": "Overdue" if is_overdue and m.status == "Scheduled" else m.status,
        "priority": m.priority,
        "cost": m.cost or 0.0,
        "mileage": m.mileage,
        "service_center": m.service_center,
        "notes": m.notes,
        "created_at": m.created_at,
        "updated_at": m.updated_at,
        "is_overdue": is_overdue,
        "days_until_due": days_until_due,
        "history_count": len(m.history) if m.history else 0
    }


# ========================================================
# CRUD & SCHEDULE ENDPOINTS
# ========================================================

@router.get("", response_model=List[MaintenanceResponse])
def list_maintenance_records(
    db: Session = Depends(get_db),
    user: User = Depends(roles("Administrator", "Fleet Manager", "Dispatcher", "Driver")),
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    vehicle_id: Optional[int] = Query(None)
):
    query = db.query(MaintenanceRecord)

    if status and status != "All":
        if status == "Overdue":
            now = datetime.utcnow()
            query = query.filter(
                or_(
                    MaintenanceRecord.status == "Overdue",
                    (MaintenanceRecord.status.in_(["Scheduled", "In Progress"]) & (MaintenanceRecord.scheduled_date < now))
                )
            )
        else:
            query = query.filter(MaintenanceRecord.status == status)

    if category and category != "All":
        query = query.filter(MaintenanceRecord.category == category)

    if priority and priority != "All":
        query = query.filter(MaintenanceRecord.priority == priority)

    if vehicle_id:
        query = query.filter(MaintenanceRecord.vehicle_id == vehicle_id)

    records = query.order_by(MaintenanceRecord.scheduled_date.asc()).all()
    return [format_maintenance(r) for r in records]


@router.post("", response_model=MaintenanceResponse, status_code=status.HTTP_201_CREATED)
def create_maintenance_record(
    data: MaintenanceCreate,
    db: Session = Depends(get_db),
    user: User = Depends(roles("Administrator", "Fleet Manager"))
):
    # Verify vehicle exists
    vehicle = db.query(Vehicle).filter(Vehicle.id == data.vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    # Validate category
    if data.category not in VALID_MAINTENANCE_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category '{data.category}'. Allowed categories: {VALID_MAINTENANCE_CATEGORIES}"
        )

    # Validate priority
    if data.priority and data.priority not in VALID_MAINTENANCE_PRIORITIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid priority '{data.priority}'. Allowed: {VALID_MAINTENANCE_PRIORITIES}"
        )

    now = datetime.utcnow()
    sched_dt = ensure_naive_utc(data.scheduled_date)
    initial_status = "Overdue" if sched_dt and sched_dt < now else "Scheduled"
    mid = f"MNT-{uuid.uuid4().hex[:6].upper()}"

    record = MaintenanceRecord(
        maintenance_id=mid,
        vehicle_id=data.vehicle_id,
        category=data.category,
        description=data.description,
        scheduled_date=sched_dt,
        status=initial_status,
        priority=data.priority or "Medium",
        cost=max(data.cost or 0.0, 0.0),
        mileage=data.mileage,
        service_center=data.service_center,
        notes=data.notes,
        created_at=now,
        updated_at=now
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    # Audit into history
    history = MaintenanceHistory(
        maintenance_id=record.id,
        vehicle_id=record.vehicle_id,
        event_type="Service Scheduled",
        previous_status=None,
        new_status=initial_status,
        cost=record.cost,
        notes=f"Scheduled {record.category} on {record.scheduled_date.strftime('%Y-%m-%d')}. Initial status: {initial_status}.",
        created_at=now
    )
    db.add(history)
    db.commit()

    return format_maintenance(record)


@router.get("/summary", response_model=MaintenanceSummaryResponse)
def get_maintenance_summary(
    db: Session = Depends(get_db),
    user: User = Depends(roles("Administrator", "Fleet Manager", "Dispatcher", "Driver"))
):
    now = datetime.utcnow()
    records = db.query(MaintenanceRecord).all()

    total = len(records)
    scheduled = sum(1 for r in records if r.status == "Scheduled" and ensure_naive_utc(r.scheduled_date) and ensure_naive_utc(r.scheduled_date) >= now)
    in_prog = sum(1 for r in records if r.status == "In Progress")
    completed = sum(1 for r in records if r.status == "Completed")
    overdue = sum(1 for r in records if r.status == "Overdue" or (r.status in ["Scheduled", "In Progress"] and ensure_naive_utc(r.scheduled_date) and ensure_naive_utc(r.scheduled_date) < now))
    cancelled = sum(1 for r in records if r.status == "Cancelled")
    total_cost = sum(r.cost for r in records if r.cost)

    cost_by_cat = {cat: 0.0 for cat in VALID_MAINTENANCE_CATEGORIES}
    count_by_cat = {cat: 0 for cat in VALID_MAINTENANCE_CATEGORIES}
    for r in records:
        if r.category in cost_by_cat:
            cost_by_cat[r.category] += (r.cost or 0.0)
            count_by_cat[r.category] += 1

    # Overdue list
    overdue_recs = [
        format_maintenance(r) for r in records
        if r.status == "Overdue" or (r.status in ["Scheduled", "In Progress"] and ensure_naive_utc(r.scheduled_date) and ensure_naive_utc(r.scheduled_date) < now)
    ]

    # Upcoming list (next 14 days)
    upcoming_limit = now + timedelta(days=14)
    upcoming_recs = [
        format_maintenance(r) for r in records
        if r.status == "Scheduled" and ensure_naive_utc(r.scheduled_date) and now <= ensure_naive_utc(r.scheduled_date) <= upcoming_limit
    ]

    urgent_count = sum(1 for r in records if r.priority in ["High", "Urgent"] and r.status in ["Scheduled", "In Progress", "Overdue"])

    # Maintenance summary aggregated by vehicle asset
    vehicles = db.query(Vehicle).all()
    by_vehicle = []
    for v in vehicles:
        v_recs = [r for r in records if r.vehicle_id == v.id]
        if v_recs:
            by_vehicle.append({
                "vehicle_id": v.id,
                "vehicle_code": v.vehicle_id,
                "registration_number": v.registration_number,
                "total_services": len(v_recs),
                "total_cost": round(sum(r.cost for r in v_recs if r.cost), 2),
                "latest_status": v_recs[-1].status
            })

    return {
        "total_records": total,
        "scheduled_count": scheduled,
        "in_progress_count": in_prog,
        "completed_count": completed,
        "overdue_count": overdue,
        "cancelled_count": cancelled,
        "total_maintenance_cost": round(total_cost, 2),
        "records_by_category": count_by_cat,
        "cost_by_category": {k: round(v, 2) for k, v in cost_by_cat.items()},
        "urgent_alerts_count": urgent_count,
        "upcoming_maintenance": upcoming_recs[:5],
        "overdue_maintenance": overdue_recs[:5],
        "maintenance_by_vehicle": by_vehicle
    }


@router.get("/alerts", response_model=List[MaintenanceAlertResponse])
def get_maintenance_alerts(
    db: Session = Depends(get_db),
    user: User = Depends(roles("Administrator", "Fleet Manager", "Dispatcher", "Driver"))
):
    """
    Generate proactive maintenance alerts from real database records.
    """
    now = datetime.utcnow()
    records = db.query(MaintenanceRecord).filter(
        MaintenanceRecord.status.in_(["Scheduled", "In Progress", "Overdue"])
    ).all()

    alerts = []
    for r in records:
        v_code = r.vehicle.vehicle_id if r.vehicle else "UNKNOWN"
        reg = r.vehicle.registration_number if r.vehicle else "N/A"
        sched_dt = ensure_naive_utc(r.scheduled_date)
        date_str = sched_dt.strftime("%Y-%m-%d") if sched_dt else "N/A"

        # Overdue check
        if r.status == "Overdue" or (sched_dt and sched_dt < now):
            days_past = (now.date() - sched_dt.date()).days if sched_dt else 0
            alerts.append({
                "id": r.id,
                "maintenance_id": r.maintenance_id,
                "vehicle_id": r.vehicle_id,
                "vehicle_code": v_code,
                "registration_number": reg,
                "category": r.category,
                "scheduled_date": r.scheduled_date,
                "priority": r.priority,
                "status": "Overdue",
                "alert_type": "Overdue Service",
                "severity": "critical",
                "message": f"{r.category} for {v_code} ({reg}) is overdue by {days_past} day(s). Scheduled: {date_str}."
            })
        # Due soon check (within 48 hours)
        elif sched_dt and sched_dt <= now + timedelta(days=2):
            hours_left = int((sched_dt - now).total_seconds() / 3600)
            alerts.append({
                "id": r.id,
                "maintenance_id": r.maintenance_id,
                "vehicle_id": r.vehicle_id,
                "vehicle_code": v_code,
                "registration_number": reg,
                "category": r.category,
                "scheduled_date": r.scheduled_date,
                "priority": r.priority,
                "status": r.status,
                "alert_type": "Due Soon",
                "severity": "warning",
                "message": f"{r.category} for {v_code} is due in ~{max(hours_left, 1)} hours ({date_str})."
            })
        # Urgent priority check
        elif r.priority in ["High", "Urgent"]:
            alerts.append({
                "id": r.id,
                "maintenance_id": r.maintenance_id,
                "vehicle_id": r.vehicle_id,
                "vehicle_code": v_code,
                "registration_number": reg,
                "category": r.category,
                "scheduled_date": r.scheduled_date,
                "priority": r.priority,
                "status": r.status,
                "alert_type": f"{r.priority} Priority Service",
                "severity": "warning" if r.priority == "High" else "critical",
                "message": f"{r.priority} priority {r.category} scheduled for {v_code} ({reg}) on {date_str}."
            })

    return alerts


@router.get("/upcoming", response_model=List[MaintenanceResponse])
def get_upcoming_maintenance(
    db: Session = Depends(get_db),
    user: User = Depends(roles("Administrator", "Fleet Manager", "Dispatcher", "Driver"))
):
    now = datetime.utcnow()
    records = db.query(MaintenanceRecord).filter(
        MaintenanceRecord.status == "Scheduled",
        MaintenanceRecord.scheduled_date >= now
    ).order_by(MaintenanceRecord.scheduled_date.asc()).all()
    return [format_maintenance(r) for r in records]


@router.get("/overdue", response_model=List[MaintenanceResponse])
def get_overdue_maintenance(
    db: Session = Depends(get_db),
    user: User = Depends(roles("Administrator", "Fleet Manager", "Dispatcher", "Driver"))
):
    now = datetime.utcnow()
    records = db.query(MaintenanceRecord).filter(
        or_(
            MaintenanceRecord.status == "Overdue",
            (MaintenanceRecord.status.in_(["Scheduled", "In Progress"]) & (MaintenanceRecord.scheduled_date < now))
        )
    ).order_by(MaintenanceRecord.scheduled_date.asc()).all()
    return [format_maintenance(r) for r in records]


@router.get("/vehicle/{vehicle_id}/history", response_model=List[MaintenanceHistoryResponse])
def get_vehicle_maintenance_history(
    vehicle_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(roles("Administrator", "Fleet Manager", "Dispatcher", "Driver"))
):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    history = db.query(MaintenanceHistory).filter(
        MaintenanceHistory.vehicle_id == vehicle_id
    ).order_by(MaintenanceHistory.created_at.desc()).all()

    return history


@router.get("/{identifier}/history", response_model=List[MaintenanceHistoryResponse])
def get_single_maintenance_history(
    identifier: str,
    db: Session = Depends(get_db),
    user: User = Depends(roles("Administrator", "Fleet Manager", "Dispatcher", "Driver"))
):
    query = db.query(MaintenanceRecord)
    if identifier.isdigit():
        record = query.filter(or_(MaintenanceRecord.id == int(identifier), MaintenanceRecord.maintenance_id == identifier)).first()
    else:
        record = query.filter(MaintenanceRecord.maintenance_id == identifier).first()

    if not record:
        raise HTTPException(status_code=404, detail="Maintenance record not found")

    history = db.query(MaintenanceHistory).filter(
        MaintenanceHistory.maintenance_id == record.id
    ).order_by(MaintenanceHistory.created_at.desc()).all()

    return history


@router.get("/{identifier}", response_model=MaintenanceResponse)
def get_maintenance_record(
    identifier: str,
    db: Session = Depends(get_db),
    user: User = Depends(roles("Administrator", "Fleet Manager", "Dispatcher", "Driver"))
):
    query = db.query(MaintenanceRecord)
    if identifier.isdigit():
        record = query.filter(or_(MaintenanceRecord.id == int(identifier), MaintenanceRecord.maintenance_id == identifier)).first()
    else:
        record = query.filter(MaintenanceRecord.maintenance_id == identifier).first()

    if not record:
        raise HTTPException(status_code=404, detail="Maintenance record not found")

    return format_maintenance(record)


@router.put("/{identifier}", response_model=MaintenanceResponse)
def update_maintenance_record(
    identifier: str,
    data: MaintenanceUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(roles("Administrator", "Fleet Manager"))
):
    query = db.query(MaintenanceRecord)
    if identifier.isdigit():
        record = query.filter(or_(MaintenanceRecord.id == int(identifier), MaintenanceRecord.maintenance_id == identifier)).first()
    else:
        record = query.filter(MaintenanceRecord.maintenance_id == identifier).first()

    if not record:
        raise HTTPException(status_code=404, detail="Maintenance record not found")

    if data.category:
        if data.category not in VALID_MAINTENANCE_CATEGORIES:
            raise HTTPException(status_code=400, detail=f"Invalid category: {data.category}")
        record.category = data.category

    if data.priority:
        if data.priority not in VALID_MAINTENANCE_PRIORITIES:
            raise HTTPException(status_code=400, detail=f"Invalid priority: {data.priority}")
        record.priority = data.priority

    if data.description is not None:
        record.description = data.description
    if data.scheduled_date is not None:
        record.scheduled_date = ensure_naive_utc(data.scheduled_date)
    if data.service_date is not None:
        record.service_date = ensure_naive_utc(data.service_date)
    if data.cost is not None:
        record.cost = max(data.cost, 0.0)
    if data.mileage is not None:
        record.mileage = data.mileage
    if data.service_center is not None:
        record.service_center = data.service_center
    if data.notes is not None:
        record.notes = data.notes

    record.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(record)

    return format_maintenance(record)


@router.put("/{identifier}/status", response_model=MaintenanceResponse)
def update_maintenance_status(
    identifier: str,
    data: MaintenanceStatusUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(roles("Administrator", "Fleet Manager"))
):
    target_status = data.status.strip()
    if target_status not in VALID_MAINTENANCE_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status '{target_status}'. Must be one of: {VALID_MAINTENANCE_STATUSES}"
        )

    query = db.query(MaintenanceRecord)
    if identifier.isdigit():
        record = query.filter(or_(MaintenanceRecord.id == int(identifier), MaintenanceRecord.maintenance_id == identifier)).first()
    else:
        record = query.filter(MaintenanceRecord.maintenance_id == identifier).first()

    if not record:
        raise HTTPException(status_code=404, detail="Maintenance record not found")

    prev_status = record.status
    record.status = target_status
    now = datetime.utcnow()
    record.updated_at = now

    if data.cost is not None:
        record.cost = max(data.cost, 0.0)

    if data.service_date:
        record.service_date = ensure_naive_utc(data.service_date)
    elif target_status in ["Completed", "In Progress"] and not record.service_date:
        record.service_date = now

    # Update Vehicle current_status accordingly
    if record.vehicle:
        if target_status == "In Progress":
            record.vehicle.current_status = "Maintenance"
        elif target_status in ["Completed", "Cancelled"] and record.vehicle.current_status == "Maintenance":
            record.vehicle.current_status = "Available"

    # Audit into history
    history = MaintenanceHistory(
        maintenance_id=record.id,
        vehicle_id=record.vehicle_id,
        event_type="Status Changed",
        previous_status=prev_status,
        new_status=target_status,
        cost=record.cost,
        notes=data.notes or f"Maintenance transitioned from {prev_status} to {target_status} by {user.role}.",
        created_at=now
    )
    db.add(history)
    db.commit()
    db.refresh(record)

    return format_maintenance(record)


@router.delete("/{identifier}")
def cancel_maintenance_record(
    identifier: str,
    db: Session = Depends(get_db),
    user: User = Depends(roles("Administrator", "Fleet Manager"))
):
    query = db.query(MaintenanceRecord)
    if identifier.isdigit():
        record = query.filter(or_(MaintenanceRecord.id == int(identifier), MaintenanceRecord.maintenance_id == identifier)).first()
    else:
        record = query.filter(MaintenanceRecord.maintenance_id == identifier).first()

    if not record:
        raise HTTPException(status_code=404, detail="Maintenance record not found")

    # If vehicle was in maintenance, release it back to Available
    if record.vehicle and record.vehicle.current_status == "Maintenance":
        record.vehicle.current_status = "Available"

    record.status = "Cancelled"
    record.updated_at = datetime.utcnow()

    history = MaintenanceHistory(
        maintenance_id=record.id,
        vehicle_id=record.vehicle_id,
        event_type="Service Cancelled",
        previous_status="Cancelled",
        new_status="Cancelled",
        cost=record.cost,
        notes=f"Maintenance cancelled by {user.role}.",
        created_at=datetime.utcnow()
    )
    db.add(history)
    db.commit()

    return {"message": f"Maintenance record {record.maintenance_id} successfully cancelled"}
