from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


# ==========================================
# AUTH SCHEMAS
# ==========================================

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    email: Optional[str] = None
    user_id: Optional[int] = None


# ==========================================
# DRIVER SCHEMAS
# ==========================================

class DriverCreate(BaseModel):
    driver_id: str = Field(min_length=2, max_length=50)
    name: str = Field(min_length=2, max_length=120)
    license_number: str = Field(min_length=2, max_length=100)
    phone: str = Field(min_length=5, max_length=30)


class DriverResponse(BaseModel):
    id: int
    driver_id: str
    name: str
    license_number: str
    phone: str
    attendance: float
    performance: float
    is_active: bool
    assigned_vehicle: Optional[str] = None

    class Config:
        from_attributes = True


# ==========================================
# VEHICLE SCHEMAS
# ==========================================

class VehicleCreate(BaseModel):
    vehicle_id: str = Field(min_length=2, max_length=50)
    registration_number: str = Field(min_length=2, max_length=50)
    vehicle_type: str = Field(min_length=2, max_length=80)
    capacity: float = Field(gt=0)
    fuel_type: str = Field(min_length=2, max_length=40)
    current_status: str = "Available"
    driver_id: Optional[int] = None


class VehicleStatusUpdate(BaseModel):
    current_status: str
    driver_id: Optional[int] = None


class VehicleResponse(BaseModel):
    id: int
    vehicle_id: str
    registration_number: str
    vehicle_type: str
    capacity: float
    fuel_type: str
    current_status: str
    driver_id: Optional[int] = None
    driver_name: Optional[str] = None

    class Config:
        from_attributes = True


# ==========================================
# SHIPMENT SCHEMAS & ENUMS
# ==========================================

VALID_SHIPMENT_STATUSES = [
    "Created",
    "Assigned",
    "In Transit",
    "Delayed",
    "Delivered",
    "Cancelled"
]

VALID_TRIP_STATUSES = [
    "Scheduled",
    "Started",
    "In Transit",
    "Completed",
    "Cancelled"
]

VALID_TRAFFIC_LEVELS = [
    "Low",
    "Moderate",
    "High",
    "Severe"
]

VALID_ROUTE_TYPES = [
    "Shortest Route",
    "Fastest Route",
    "Traffic Avoidance",
    "Fuel Efficient Route"
]


class ShipmentCreate(BaseModel):
    shipment_id: Optional[str] = None
    tracking_number: Optional[str] = None
    customer_name: str = Field(default="Acme Logistics", min_length=2, max_length=120)
    customer_phone: Optional[str] = None
    origin: str = Field(min_length=2, max_length=255)
    destination: str = Field(min_length=2, max_length=255)
    description: Optional[str] = None
    scheduled_pickup: Optional[datetime] = None
    scheduled_delivery: Optional[datetime] = None
    vehicle_id: Optional[int] = None
    driver_id: Optional[int] = None
    route_type: Optional[str] = "Fastest Route"
    traffic_level: Optional[str] = "Moderate"


class ShipmentUpdate(BaseModel):
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    description: Optional[str] = None
    scheduled_pickup: Optional[datetime] = None
    scheduled_delivery: Optional[datetime] = None
    expected_delivery: Optional[datetime] = None
    route_type: Optional[str] = None
    traffic_level: Optional[str] = None


class ShipmentStatusUpdate(BaseModel):
    status: str
    description: Optional[str] = None
    location_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    progress: Optional[float] = None


class ShipmentAssign(BaseModel):
    vehicle_id: Optional[int] = None
    driver_id: Optional[int] = None


class ShipmentHistoryResponse(BaseModel):
    id: int
    shipment_id: int
    event_type: str
    previous_status: Optional[str] = None
    new_status: Optional[str] = None
    status: str
    current_location: Optional[str] = None
    progress: float
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    expected_delivery: Optional[datetime] = None
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ShipmentResponse(BaseModel):
    id: int
    shipment_id: str
    tracking_number: str
    customer_name: str
    customer_phone: Optional[str] = None
    origin: str
    destination: str
    description: Optional[str] = None
    status: str
    current_location: Optional[str] = None
    due_date: Optional[datetime] = None
    expected_delivery: Optional[datetime] = None
    scheduled_pickup: Optional[datetime] = None
    scheduled_delivery: Optional[datetime] = None
    actual_delivery: Optional[datetime] = None
    vehicle_id: Optional[int] = None
    driver_id: Optional[int] = None
    progress: float
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    distance_km: float
    estimated_duration: Optional[str] = None
    route_type: str
    traffic_level: str
    created_at: datetime
    updated_at: datetime
    vehicle_info: Optional[Dict[str, Any]] = None
    driver_info: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


# ==========================================
# TRIP SCHEMAS
# ==========================================

class TripCreate(BaseModel):
    trip_id: Optional[str] = None
    shipment_id: Optional[int] = None
    vehicle_id: int
    driver_id: int
    origin: str = Field(min_length=2, max_length=255)
    destination: str = Field(min_length=2, max_length=255)
    route_type: Optional[str] = "Fastest Route"
    distance_km: Optional[float] = 0.0
    scheduled_start: Optional[datetime] = None
    scheduled_arrival: Optional[datetime] = None
    notes: Optional[str] = None


class TripStatusUpdate(BaseModel):
    trip_status: str
    notes: Optional[str] = None


class TripResponse(BaseModel):
    id: int
    trip_id: str
    shipment_id: Optional[int] = None
    vehicle_id: int
    driver_id: int
    origin: str
    destination: str
    trip_status: str
    route_type: str
    distance_km: float
    scheduled_start: Optional[datetime] = None
    scheduled_arrival: Optional[datetime] = None
    actual_start: Optional[datetime] = None
    actual_arrival: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    vehicle_code: Optional[str] = None
    driver_name: Optional[str] = None
    shipment_code: Optional[str] = None

    class Config:
        from_attributes = True


# ==========================================
# TRACKING & GPS SCHEMAS
# ==========================================

class LocationUpdate(BaseModel):
    latitude: float
    longitude: float
    location_name: Optional[str] = None
    progress: Optional[float] = None
    speed_kmh: Optional[float] = 45.0
    timestamp: Optional[datetime] = None


class TrackingTelemetryResponse(BaseModel):
    shipment_id: str
    tracking_number: str
    status: str
    origin: str
    destination: str
    current_location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    progress: float
    distance_km: float
    remaining_km: float
    estimated_duration: Optional[str] = None
    eta: Optional[str] = None
    traffic_level: str
    gps_status: str
    last_update: datetime
    vehicle_info: Optional[Dict[str, Any]] = None
    driver_info: Optional[Dict[str, Any]] = None


# ==========================================
# ROUTE OPTIMIZATION SCHEMAS
# ==========================================

class RouteCalculationRequest(BaseModel):
    origin: str = Field(min_length=2, max_length=255)
    destination: str = Field(min_length=2, max_length=255)
    traffic_level: Optional[str] = "Moderate"
    vehicle_type: Optional[str] = "Truck"


class RouteOption(BaseModel):
    route_type: str
    name: str
    distance_km: float
    travel_time_minutes: int
    duration_text: str
    traffic_level: str
    eta_time: str
    fuel_estimate_liters: float
    co2_emissions_kg: float
    description: str
    waypoints: List[Dict[str, Any]]


class RouteCalculationResponse(BaseModel):
    origin: str
    destination: str
    traffic_level: str
    vehicle_type: str
    routes: List[RouteOption]
    recommended_route: str