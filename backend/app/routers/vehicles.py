from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Vehicle, Driver, User
from ..schemas import VehicleCreate, VehicleResponse, VehicleStatusUpdate
from ..auth import roles

router = APIRouter(prefix="/api/vehicles", tags=["Fleet Management"])


def format_vehicle(v: Vehicle) -> dict:
    return {
        "id": v.id,
        "vehicle_id": v.vehicle_id,
        "registration_number": v.registration_number,
        "vehicle_type": v.vehicle_type,
        "capacity": v.capacity,
        "fuel_type": v.fuel_type,
        "current_status": v.current_status,
        "driver_id": v.driver_id,
        "driver_name": v.driver.name if v.driver else None
    }


@router.get("", response_model=list[VehicleResponse])
def list_vehicles(
    db: Session = Depends(get_db),
    user: User = Depends(roles("Administrator", "Fleet Manager", "Dispatcher", "Driver"))
):
    vehicles = db.query(Vehicle).order_by(Vehicle.id.desc()).all()
    return [format_vehicle(v) for v in vehicles]


@router.post("", response_model=VehicleResponse)
def create_vehicle(
    data: VehicleCreate,
    db: Session = Depends(get_db),
    user: User = Depends(roles("Administrator", "Fleet Manager"))
):
    clean_vid = data.vehicle_id.strip()
    clean_reg = data.registration_number.strip()

    if db.query(Vehicle).filter(Vehicle.vehicle_id == clean_vid).first():
        raise HTTPException(status_code=409, detail="Vehicle ID already exists")
    if db.query(Vehicle).filter(Vehicle.registration_number == clean_reg).first():
        raise HTTPException(status_code=409, detail="Registration number already exists")
    if data.driver_id and not db.query(Driver).filter(Driver.id == data.driver_id).first():
        raise HTTPException(status_code=404, detail="Driver not found")

    payload = data.model_dump()
    payload["vehicle_id"] = clean_vid
    payload["registration_number"] = clean_reg
    payload["vehicle_type"] = data.vehicle_type.strip()
    payload["fuel_type"] = data.fuel_type.strip()

    item = Vehicle(**payload)
    db.add(item)
    db.commit()
    db.refresh(item)
    return format_vehicle(item)


@router.put("/{vehicle_id}/status", response_model=VehicleResponse)
def update_vehicle_status(
    vehicle_id: str,
    data: VehicleStatusUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(roles("Administrator", "Fleet Manager", "Dispatcher"))
):
    vehicle = db.query(Vehicle).filter(Vehicle.id == int(vehicle_id) if vehicle_id.isdigit() else Vehicle.vehicle_id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    valid_statuses = ["Available", "Active", "Maintenance"]
    if data.current_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid vehicle status. Must be one of: {valid_statuses}")

    vehicle.current_status = data.current_status
    if data.driver_id is not None:
        if data.driver_id > 0:
            if not db.query(Driver).filter(Driver.id == data.driver_id).first():
                raise HTTPException(status_code=404, detail="Driver not found")
            vehicle.driver_id = data.driver_id
        else:
            vehicle.driver_id = None

    db.commit()
    db.refresh(vehicle)
    return format_vehicle(vehicle)
