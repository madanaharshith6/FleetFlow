from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Driver
from ..schemas import DriverCreate, DriverResponse
from ..auth import roles

router = APIRouter(prefix="/api/drivers", tags=["Drivers"])

@router.get("", response_model=list[DriverResponse])
def list_drivers(
    db: Session = Depends(get_db),
    user=Depends(roles("Administrator", "Fleet Manager", "Dispatcher", "Driver"))
):
    return db.query(Driver).order_by(Driver.id.desc()).all()

@router.post("", response_model=DriverResponse)
def create_driver(
    data: DriverCreate,
    db: Session = Depends(get_db),
    user=Depends(roles("Administrator", "Fleet Manager"))
):
    if db.query(Driver).filter(Driver.driver_id == data.driver_id).first():
        raise HTTPException(status_code=409, detail="Driver ID already exists")
    item = Driver(**data.model_dump())
    db.add(item); db.commit(); db.refresh(item)
    return item
