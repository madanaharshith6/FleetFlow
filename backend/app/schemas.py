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


class ShipmentRecalculateRoute(BaseModel):
    traffic_level: Optional[str] = "Moderate"
    route_type: Optional[str] = None


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


# ==========================================
# MILESTONE 3: MAINTENANCE SCHEMAS
# ==========================================

VALID_MAINTENANCE_CATEGORIES = [
    "Oil Change",
    "Tire Replacement",
    "Engine Service",
    "Brake Service",
    "General Inspection"
]

VALID_MAINTENANCE_STATUSES = [
    "Scheduled",
    "In Progress",
    "Completed",
    "Overdue",
    "Cancelled"
]

VALID_MAINTENANCE_PRIORITIES = [
    "Low",
    "Medium",
    "High",
    "Urgent"
]


class MaintenanceCreate(BaseModel):
    vehicle_id: int
    category: str = Field(min_length=2, max_length=60)
    description: Optional[str] = Field(default=None, max_length=255)
    scheduled_date: datetime
    priority: Optional[str] = "Medium"
    cost: Optional[float] = 0.0
    mileage: Optional[float] = None
    service_center: Optional[str] = Field(default=None, max_length=120)
    notes: Optional[str] = Field(default=None, max_length=255)


class MaintenanceUpdate(BaseModel):
    category: Optional[str] = None
    description: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    service_date: Optional[datetime] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    cost: Optional[float] = None
    mileage: Optional[float] = None
    service_center: Optional[str] = None
    notes: Optional[str] = None


class MaintenanceStatusUpdate(BaseModel):
    status: str
    notes: Optional[str] = None
    cost: Optional[float] = None
    service_date: Optional[datetime] = None


class MaintenanceHistoryResponse(BaseModel):
    id: int
    maintenance_id: int
    vehicle_id: int
    event_type: str
    previous_status: Optional[str] = None
    new_status: str
    cost: Optional[float] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class MaintenanceResponse(BaseModel):
    id: int
    maintenance_id: str
    vehicle_id: int
    vehicle_code: Optional[str] = None
    registration_number: Optional[str] = None
    vehicle_type: Optional[str] = None
    category: str
    description: Optional[str] = None
    scheduled_date: datetime
    service_date: Optional[datetime] = None
    status: str
    priority: str
    cost: float
    mileage: Optional[float] = None
    service_center: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_overdue: bool = False
    days_until_due: Optional[int] = None
    history_count: int = 0

    class Config:
        from_attributes = True


class MaintenanceAlertResponse(BaseModel):
    id: int
    maintenance_id: str
    vehicle_id: int
    vehicle_code: str
    registration_number: str
    category: str
    scheduled_date: datetime
    priority: str
    status: str
    alert_type: str  # "Overdue", "Due Soon", "Urgent Priority"
    severity: str    # "critical", "warning", "info"
    message: str


class MaintenanceSummaryResponse(BaseModel):
    total_records: int
    scheduled_count: int
    in_progress_count: int
    completed_count: int
    overdue_count: int
    cancelled_count: int
    total_maintenance_cost: float
    records_by_category: Dict[str, int]
    cost_by_category: Dict[str, float]
    urgent_alerts_count: int
    upcoming_maintenance: List[MaintenanceResponse]
    overdue_maintenance: List[MaintenanceResponse]
    maintenance_by_vehicle: Optional[List[Dict[str, Any]]] = None


# ==========================================
# MILESTONE 3: DRIVER ASSIGNMENT SCHEMAS
# ==========================================

class DriverAssignVehicle(BaseModel):
    vehicle_id: Optional[int] = None
    notes: Optional[str] = None


class DriverMonitoringResponse(BaseModel):
    id: int
    driver_id: str
    name: str
    license_number: str
    phone: str
    attendance: float
    performance: float
    is_active: bool
    assigned_vehicle_id: Optional[int] = None
    assigned_vehicle_code: Optional[str] = None
    assigned_registration: Optional[str] = None
    total_trips: int = 0
    active_trips: int = 0
    completed_trips: int = 0
    status_label: str = "Available"

    class Config:
        from_attributes = True


# ==========================================
# MILESTONE 3: ANALYTICS SCHEMAS
# ==========================================

class FleetKPIs(BaseModel):
    total_vehicles: int
    active_vehicles: int
    available_vehicles: int
    maintenance_vehicles: int
    inactive_vehicles: int
    fleet_utilization_percent: float
    utilization_formula: str


class DriverKPIs(BaseModel):
    total_drivers: int
    active_drivers: int
    assigned_drivers: int
    unassigned_drivers: int
    average_attendance: float
    average_performance: float


class ShipmentKPIs(BaseModel):
    total_shipments: int
    active_shipments: int
    delivered_shipments: int
    delayed_shipments: int
    cancelled_shipments: int
    completion_rate_percent: float


class TripKPIs(BaseModel):
    total_trips: int
    scheduled_trips: int
    in_transit_trips: int
    completed_trips: int


class MaintenanceKPIs(BaseModel):
    total_records: int
    scheduled_records: int
    in_progress_records: int
    completed_records: int
    overdue_records: int
    total_expenditure: float


class OperationalAnalyticsResponse(BaseModel):
    fleet: FleetKPIs
    drivers: DriverKPIs
    shipments: ShipmentKPIs
    trips: TripKPIs
    maintenance: MaintenanceKPIs
    generated_at: datetime


class VehicleFuelMetric(BaseModel):
    vehicle_id: str
    registration: str
    vehicle_type: str
    trips_completed: int
    total_distance_km: float
    estimated_fuel_liters: float
    fuel_efficiency_kpl: float
    estimated_fuel_cost: float


class FuelAnalyticsResponse(BaseModel):
    total_distance_logged_km: float
    total_fuel_consumed_liters: float
    total_fuel_cost_estimated: float
    average_fleet_efficiency_kpl: float
    fuel_by_vehicle_type: Dict[str, Dict[str, float]]
    vehicle_rankings: List[VehicleFuelMetric]
    corridor_fuel_breakdown: List[Dict[str, Any]]
    methodology: str


# ==========================================
# MILESTONE 3: CELERY TASK SCHEMAS
# ==========================================

class CeleryTaskTriggerResponse(BaseModel):
    task_id: str
    task_name: str
    status: str
    message: str
    timestamp: datetime