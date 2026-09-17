from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="Administrator")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

class Driver(Base):
    __tablename__ = "drivers"
    id = Column(Integer, primary_key=True)
    driver_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(120), nullable=False)
    license_number = Column(String(100), nullable=False)
    phone = Column(String(30), nullable=False)
    attendance = Column(Float, nullable=False, default=100)
    performance = Column(Float, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    vehicles = relationship("Vehicle", back_populates="driver")

class Vehicle(Base):
    __tablename__ = "vehicles"
    id = Column(Integer, primary_key=True)
    vehicle_id = Column(String(50), unique=True, nullable=False, index=True)
    registration_number = Column(String(50), unique=True, nullable=False)
    vehicle_type = Column(String(80), nullable=False)
    capacity = Column(Float, nullable=False)
    fuel_type = Column(String(40), nullable=False)
    current_status = Column(String(40), nullable=False, default="Available")
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    driver = relationship("Driver", back_populates="vehicles")
