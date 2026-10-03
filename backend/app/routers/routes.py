from fastapi import APIRouter, Depends, HTTPException
from ..auth import roles
from ..models import User
from ..schemas import RouteCalculationRequest, RouteCalculationResponse
from ..services.route_optimizer import calculate_routes


router = APIRouter(
    prefix="/api/routes",
    tags=["Route Optimization"]
)


@router.post("/calculate", response_model=RouteCalculationResponse)
def calculate_optimal_routes(
    data: RouteCalculationRequest,
    user: User = Depends(roles("Administrator", "Fleet Manager", "Dispatcher", "Driver"))
):
    if not data.origin.strip() or not data.destination.strip():
        raise HTTPException(status_code=400, detail="Origin and Destination cannot be empty")

    results = calculate_routes(
        origin=data.origin.strip(),
        destination=data.destination.strip(),
        traffic_level=data.traffic_level or "Moderate",
        vehicle_type=data.vehicle_type or "Truck"
    )
    return results


@router.post("/recalculate", response_model=RouteCalculationResponse)
def recalculate_route(
    data: RouteCalculationRequest,
    user: User = Depends(roles("Administrator", "Fleet Manager", "Dispatcher", "Driver"))
):
    return calculate_routes(
        origin=data.origin.strip(),
        destination=data.destination.strip(),
        traffic_level=data.traffic_level or "High",
        vehicle_type=data.vehicle_type or "Truck"
    )
