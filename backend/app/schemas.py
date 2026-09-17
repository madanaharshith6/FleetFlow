from typing import Optional
from pydantic import BaseModel, EmailStr, Field

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str

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
    class Config:
        from_attributes = True

class VehicleCreate(BaseModel):
    vehicle_id: str = Field(min_length=2, max_length=50)
    registration_number: str = Field(min_length=2, max_length=50)
    vehicle_type: str
    capacity: float = Field(gt=0)
    fuel_type: str
    current_status: str = "Available"
    driver_id: Optional[int] = None

class VehicleResponse(BaseModel):
    id: int
    vehicle_id: str
    registration_number: str
    vehicle_type: str
    capacity: float
    fuel_type: str
    current_status: str
    driver_id: Optional[int]
    class Config:
        from_attributes = True
