from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Driver, User
from ..schemas import DriverCreate, DriverResponse
from ..auth import roles

router = APIRouter(prefix="/api/drivers", tags=["Drivers"])


def format_driver(d: Driver) -> dict:
    assigned_veh = None
    if d.vehicles:
        assigned_veh = f"{d.vehicles[0].vehicle_id} ({d.vehicles[0].registration_number})"

    return {
        "id": d.id,
        "driver_id": d.driver_id,
        "name": d.name,
        "license_number": d.license_number,
        "phone": d.phone,
        "attendance": d.attendance,
        "performance": d.performance,
        "is_active": d.is_active,
        "assigned_vehicle": assigned_veh
    }


@router.get("", response_model=list[DriverResponse])
def list_drivers(
    db: Session = Depends(get_db),
    user: User = Depends(roles("Administrator", "Fleet Manager", "Dispatcher", "Driver"))
):
    drivers = db.query(Driver).order_by(Driver.id.desc()).all()
    return [format_driver(d) for d in drivers]


@router.post("", response_model=DriverResponse)
def create_driver(
    data: DriverCreate,
    db: Session = Depends(get_db),
    user: User = Depends(roles("Administrator", "Fleet Manager"))
):
    clean_did = data.driver_id.strip()
    clean_name = data.name.strip()
    clean_lic = data.license_number.strip()
    clean_phone = data.phone.strip()

    if db.query(Driver).filter(Driver.driver_id == clean_did).first():
        raise HTTPException(status_code=409, detail="Driver ID already exists")

    item = Driver(
        driver_id=clean_did,
        name=clean_name,
        license_number=clean_lic,
        phone=clean_phone
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return format_driver(item)


@router.get("/monitoring", response_model=list[dict])
def monitor_drivers(
    db: Session = Depends(get_db),
    user: User = Depends(roles("Administrator", "Fleet Manager", "Dispatcher"))
):
    """
    Milestone 3 Driver Monitoring:
    Returns driver performance, attendance, assigned vehicles, and trip stats.
    """
    drivers = db.query(Driver).order_by(Driver.id.desc()).all()
    results = []
    for d in drivers:
        assigned_veh = d.vehicles[0] if d.vehicles else None
        active_trips_count = sum(1 for t in d.trips if t.trip_status in ["Started", "In Transit"])
        completed_trips_count = sum(1 for t in d.trips if t.trip_status == "Completed")

        # Determine live status label
        status_label = "Available"
        if not d.is_active:
            status_label = "Inactive"
        elif active_trips_count > 0:
            status_label = "On Trip"
        elif assigned_veh:
            status_label = "Assigned"

        results.append({
            "id": d.id,
            "driver_id": d.driver_id,
            "name": d.name,
            "license_number": d.license_number,
            "phone": d.phone,
            "attendance": d.attendance,
            "performance": d.performance,
            "is_active": d.is_active,
            "assigned_vehicle_id": assigned_veh.id if assigned_veh else None,
            "assigned_vehicle_code": assigned_veh.vehicle_id if assigned_veh else None,
            "assigned_registration": assigned_veh.registration_number if assigned_veh else None,
            "total_trips": len(d.trips),
            "active_trips": active_trips_count,
            "completed_trips": completed_trips_count,
            "status_label": status_label
        })
    return results


@router.post("/{driver_id}/assign-vehicle")
def assign_driver_vehicle(
    driver_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    user: User = Depends(roles("Administrator", "Fleet Manager", "Dispatcher"))
):
    """
    Milestone 3 Driver Assignment System:
    Assigns or updates a driver's assigned vehicle with full availability checks.
    """
    from ..models import Vehicle

    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    target_vehicle_id = payload.get("vehicle_id")
    if not target_vehicle_id:
        raise HTTPException(status_code=400, detail="vehicle_id is required")

    vehicle = db.query(Vehicle).filter(Vehicle.id == target_vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    if not driver.is_active:
        raise HTTPException(
            status_code=400,
            detail=f"Driver '{driver.name}' is inactive/on leave and cannot be assigned a vehicle."
        )

    active_trips = [t for t in driver.trips if t.trip_status in ["Started", "In Transit"]]
    if active_trips:
        raise HTTPException(
            status_code=400,
            detail=f"Driver '{driver.name}' is currently on an active trip ({active_trips[0].trip_id}) and cannot be reassigned until the trip completes."
        )

    if vehicle.current_status == "Maintenance":
        raise HTTPException(
            status_code=400,
            detail=f"Vehicle '{vehicle.vehicle_id}' is currently under Maintenance and cannot be assigned."
        )

    # Check if driver is already assigned to another vehicle; if so, release old vehicle
    for old_veh in driver.vehicles:
        old_veh.driver_id = None

    # Check if target vehicle is assigned to another driver; if so, reassign
    if vehicle.driver_id and vehicle.driver_id != driver.id:
        # Reassign from previous driver
        vehicle.driver_id = None

    vehicle.driver_id = driver.id
    db.commit()
    db.refresh(driver)
    db.refresh(vehicle)

    return {
        "message": f"Driver '{driver.name}' successfully assigned to vehicle '{vehicle.vehicle_id}' ({vehicle.registration_number})",
        "driver": format_driver(driver),
        "vehicle_id": vehicle.id,
        "vehicle_code": vehicle.vehicle_id
    }


@router.post("/{driver_id}/unassign-vehicle")
def unassign_driver_vehicle(
    driver_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(roles("Administrator", "Fleet Manager", "Dispatcher"))
):
    """
    Milestone 3 Driver Assignment System:
    Removes vehicle assignment from a driver.
    """
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    for v in driver.vehicles:
        v.driver_id = None

    db.commit()
    db.refresh(driver)

    return {
        "message": f"Driver '{driver.name}' unassigned from all vehicles",
        "driver": format_driver(driver)
    }

