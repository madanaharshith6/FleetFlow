from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Vehicle, Driver
from ..schemas import VehicleCreate, VehicleResponse
from ..auth import roles

router = APIRouter(prefix="/api/vehicles", tags=["Fleet Management"])

@router.get("", response_model=list[VehicleResponse])
def list_vehicles(
    db: Session = Depends(get_db),
    user=Depends(roles("Administrator", "Fleet Manager", "Dispatcher", "Driver"))
):
    return db.query(Vehicle).order_by(Vehicle.id.desc()).all()

@router.post("", response_model=VehicleResponse)
def create_vehicle(
    data: VehicleCreate,
    db: Session = Depends(get_db),
    user=Depends(roles("Administrator", "Fleet Manager"))
):
    if db.query(Vehicle).filter(Vehicle.vehicle_id == data.vehicle_id).first():
        raise HTTPException(status_code=409, detail="Vehicle ID already exists")
    if db.query(Vehicle).filter(Vehicle.registration_number == data.registration_number).first():
        raise HTTPException(status_code=409, detail="Registration number already exists")
    if data.driver_id and not db.query(Driver).filter(Driver.id == data.driver_id).first():
        raise HTTPException(status_code=404, detail="Driver not found")
    item = Vehicle(**data.model_dump())
    db.add(item); db.commit(); db.refresh(item)
    return item
