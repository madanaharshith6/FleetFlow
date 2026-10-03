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
