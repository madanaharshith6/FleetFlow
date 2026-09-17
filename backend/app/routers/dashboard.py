from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Vehicle, Driver
from ..auth import roles

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/summary")
def summary(
    db: Session = Depends(get_db),
    user=Depends(roles("Administrator", "Fleet Manager", "Dispatcher", "Driver"))
):
    return {
        "total_vehicles": db.query(Vehicle).count(),
        "active_vehicles": db.query(Vehicle).filter(Vehicle.current_status == "Active").count(),
        "available_vehicles": db.query(Vehicle).filter(Vehicle.current_status == "Available").count(),
        "maintenance_vehicles": db.query(Vehicle).filter(Vehicle.current_status == "Maintenance").count(),
        "active_drivers": db.query(Driver).filter(Driver.is_active == True).count()
    }
