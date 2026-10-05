from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    Boolean
)
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
    attendance = Column(Float, nullable=False, default=100.0)
    performance = Column(Float, nullable=False, default=0.0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    vehicles = relationship("Vehicle", back_populates="driver")
    shipments = relationship("Shipment", back_populates="driver")
    trips = relationship("Trip", back_populates="driver")


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
    shipments = relationship("Shipment", back_populates="vehicle")
    trips = relationship("Trip", back_populates="vehicle")
    maintenance_records = relationship("MaintenanceRecord", back_populates="vehicle", cascade="all, delete-orphan", order_by="MaintenanceRecord.scheduled_date.asc()")


class Shipment(Base):
    __tablename__ = "shipments"

    id = Column(Integer, primary_key=True)
    shipment_id = Column(String(50), unique=True, nullable=False, index=True)
    tracking_number = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)
    customer_name = Column(String(120), nullable=False, default="Acme Logistics")
    customer_phone = Column(String(30), nullable=True)
    origin = Column(String(255), nullable=False)
    destination = Column(String(255), nullable=False)
    status = Column(String(40), nullable=False, default="Created")
    current_location = Column(String(255), nullable=True)
    due_date = Column(DateTime, nullable=True)
    expected_delivery = Column(DateTime, nullable=True)
    scheduled_pickup = Column(DateTime, nullable=True)
    scheduled_delivery = Column(DateTime, nullable=True)
    actual_delivery = Column(DateTime, nullable=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=True)
    progress = Column(Float, nullable=False, default=0.0)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    distance_km = Column(Float, nullable=False, default=0.0)
    estimated_duration = Column(String(50), nullable=True)
    route_type = Column(String(50), nullable=False, default="Fastest Route")
    traffic_level = Column(String(30), nullable=False, default="Moderate")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    vehicle = relationship("Vehicle", back_populates="shipments")
    driver = relationship("Driver", back_populates="shipments")
    history = relationship("ShipmentHistory", back_populates="shipment", cascade="all, delete-orphan", order_by="ShipmentHistory.created_at.desc()")
    trips = relationship("Trip", back_populates="shipment", cascade="all, delete-orphan")


class Trip(Base):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True)
    trip_id = Column(String(50), unique=True, nullable=False, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id", ondelete="SET NULL"), nullable=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=False)
    origin = Column(String(255), nullable=False)
    destination = Column(String(255), nullable=False)
    trip_status = Column(String(40), nullable=False, default="Scheduled")
    route_type = Column(String(50), nullable=False, default="Fastest Route")
    distance_km = Column(Float, nullable=False, default=0.0)
    scheduled_start = Column(DateTime, nullable=True)
    scheduled_arrival = Column(DateTime, nullable=True)
    actual_start = Column(DateTime, nullable=True)
    actual_arrival = Column(DateTime, nullable=True)
    notes = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    shipment = relationship("Shipment", back_populates="trips")
    vehicle = relationship("Vehicle", back_populates="trips")
    driver = relationship("Driver", back_populates="trips")


class ShipmentHistory(Base):
    __tablename__ = "shipment_history"

    id = Column(Integer, primary_key=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=False)
    event_type = Column(String(80), nullable=False, default="Status Update")
    previous_status = Column(String(40), nullable=True)
    new_status = Column(String(40), nullable=True)
    status = Column(String(40), nullable=False)
    current_location = Column(String(255), nullable=True)
    progress = Column(Float, nullable=False, default=0.0)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    expected_delivery = Column(DateTime, nullable=True)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    shipment = relationship("Shipment", back_populates="history")


class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"

    id = Column(Integer, primary_key=True)
    maintenance_id = Column(String(50), unique=True, nullable=False, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False, index=True)
    category = Column(String(60), nullable=False)  # Oil Change, Tire Replacement, Engine Service, Brake Service, General Inspection
    description = Column(String(255), nullable=True)
    scheduled_date = Column(DateTime, nullable=False, index=True)
    service_date = Column(DateTime, nullable=True)
    status = Column(String(40), nullable=False, default="Scheduled", index=True)  # Scheduled, In Progress, Completed, Overdue, Cancelled
    priority = Column(String(30), nullable=False, default="Medium")  # Low, Medium, High, Urgent
    cost = Column(Float, nullable=False, default=0.0)
    mileage = Column(Float, nullable=True)
    service_center = Column(String(120), nullable=True)
    notes = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    vehicle = relationship("Vehicle", back_populates="maintenance_records")
    history = relationship("MaintenanceHistory", back_populates="maintenance_record", cascade="all, delete-orphan", order_by="MaintenanceHistory.created_at.desc()")


class MaintenanceHistory(Base):
    __tablename__ = "maintenance_history"

    id = Column(Integer, primary_key=True)
    maintenance_id = Column(Integer, ForeignKey("maintenance_records.id", ondelete="CASCADE"), nullable=False, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    event_type = Column(String(80), nullable=False, default="Status Change")
    previous_status = Column(String(40), nullable=True)
    new_status = Column(String(40), nullable=False)
    cost = Column(Float, nullable=True)
    notes = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    maintenance_record = relationship("MaintenanceRecord", back_populates="history")
    vehicle = relationship("Vehicle")