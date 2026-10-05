import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine, SessionLocal
from .models import User, Driver, Vehicle, Shipment, MaintenanceRecord, MaintenanceHistory, Trip
from .auth import hash_password
from .routers import (
    auth,
    drivers,
    vehicles,
    dashboard,
    shipments,
    trips,
    routes,
    tracking,
    websockets,
    maintenance,
    analytics,
    tasks
)

app = FastAPI(
    title="FleetFlow API – Fleet Management & Logistics Tracking Platform",
    description="Milestone 3: Maintenance Management, Driver Assignment, Analytics & Background Processing",
    version="3.0.0"
)

# CORS configuration
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "https://fleetflow-ssts.onrender.com",
]
frontend_url = os.getenv("FRONTEND_URL", "").strip()
if frontend_url and frontend_url not in origins:
    origins.append(frontend_url)
    origins.append(frontend_url.rstrip("/"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# API Routers
app.include_router(auth.router)
app.include_router(drivers.router)
app.include_router(vehicles.router)
app.include_router(dashboard.router)
app.include_router(shipments.router)
app.include_router(trips.router)
app.include_router(routes.router)
app.include_router(tracking.router)
app.include_router(websockets.router)
app.include_router(maintenance.router)
app.include_router(analytics.router)
app.include_router(tasks.router)


@app.get("/")
def root():
    return {
        "message": "FleetFlow Logistics & Fleet Management API",
        "version": "3.0.0",
        "milestone": 3,
        "features": [
            "Vehicle Maintenance Scheduling & History",
            "Proactive Maintenance Alert System",
            "Driver Assignment & Monitoring",
            "Fleet Performance & Operational Analytics",
            "Trip-Based Fuel Monitoring & Cost Estimation",
            "Celery Asynchronous Background Processing",
            "Real-Time Shipment Tracking & Route Optimization",
            "Role-Based Access Control"
        ]
    }


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Seed demo user accounts for all 4 RBAC roles
        demo_accounts = [
            ("admin@fleetflow.com", "Admin@123", "Administrator"),
            ("manager@fleetflow.com", "Admin@123", "Fleet Manager"),
            ("dispatcher@fleetflow.com", "Admin@123", "Dispatcher"),
            ("driver@fleetflow.com", "Admin@123", "Driver")
        ]

        for email, pwd, role in demo_accounts:
            existing = db.query(User).filter(User.email == email).first()
            if not existing:
                db.add(
                    User(
                        email=email,
                        password_hash=hash_password(pwd),
                        role=role
                    )
                )
        db.commit()

        # 2. Seed initial demo vehicles & drivers if none exist
        if db.query(Vehicle).count() == 0:
            demo_drivers = [
                Driver(driver_id="DRV-101", name="Ramesh Kumar", license_number="DL-0420110098765", phone="+91 98765 11223", attendance=98.5, performance=92.0),
                Driver(driver_id="DRV-102", name="Suresh Reddy", license_number="DL-0720150043210", phone="+91 98765 22334", attendance=96.0, performance=88.5),
                Driver(driver_id="DRV-103", name="Anil Varma", license_number="DL-0920180065432", phone="+91 98765 33445", attendance=100.0, performance=95.0),
            ]
            db.add_all(demo_drivers)
            db.commit()

            demo_vehicles = [
                Vehicle(vehicle_id="VEH-101", registration_number="AP09-TX-1001", vehicle_type="Truck", capacity=12000.0, fuel_type="Diesel", current_status="Active", driver_id=demo_drivers[0].id),
                Vehicle(vehicle_id="VEH-102", registration_number="TS07-EX-2002", vehicle_type="Container Truck", capacity=25000.0, fuel_type="Diesel", current_status="Available", driver_id=demo_drivers[1].id),
                Vehicle(vehicle_id="VEH-103", registration_number="KA01-VX-3003", vehicle_type="Van", capacity=3500.0, fuel_type="Diesel", current_status="Maintenance", driver_id=None),
            ]
            db.add_all(demo_vehicles)
            db.commit()

        # 3. Seed initial demo shipment if none exists
        if db.query(Shipment).count() == 0:
            v1 = db.query(Vehicle).first()
            d1 = db.query(Driver).first()
            db.add(
                Shipment(
                    shipment_id="SHP-1001",
                    tracking_number="TRK-98765432",
                    customer_name="Alpha Tech Deliveries",
                    customer_phone="+91 98765 43210",
                    origin="Vijayawada",
                    destination="Hyderabad",
                    description="Industrial electronic sensors and telemetry units",
                    status="In Transit",
                    current_location="NH65 Midway Transit Corridor",
                    latitude=16.8500,
                    longitude=79.8000,
                    progress=35.0,
                    distance_km=274.5,
                    estimated_duration="3h 15m",
                    route_type="Fastest Route",
                    traffic_level="Moderate",
                    vehicle_id=v1.id if v1 else None,
                    driver_id=d1.id if d1 else None
                )
            )
            db.commit()

        # 4. Seed initial demo maintenance records if none exist
        if db.query(MaintenanceRecord).count() == 0:
            v_all = db.query(Vehicle).all()
            if v_all:
                from datetime import datetime, timedelta
                now = datetime.utcnow()

                v1 = v_all[0]
                v2 = v_all[1] if len(v_all) > 1 else v1
                v3 = v_all[2] if len(v_all) > 2 else v1

                m1 = MaintenanceRecord(
                    maintenance_id="MNT-2001",
                    vehicle_id=v1.id,
                    category="Oil Change",
                    description="Standard 10,000 km engine synthetic oil and filter replacement",
                    scheduled_date=now + timedelta(days=3),
                    status="Scheduled",
                    priority="Medium",
                    cost=4500.0,
                    mileage=32400.0,
                    service_center="Express Fleet Works, NH65",
                    notes="Check oil pressure sensor upon completion",
                    created_at=now - timedelta(days=5),
                    updated_at=now
                )
                m2 = MaintenanceRecord(
                    maintenance_id="MNT-2002",
                    vehicle_id=v2.id,
                    category="Brake Service",
                    description="Hydraulic brake pad wear inspection and rotor resurfacing",
                    scheduled_date=now - timedelta(days=2),
                    status="Overdue",
                    priority="High",
                    cost=8200.0,
                    mileage=48100.0,
                    service_center="Central Heavy Automotive Depot",
                    notes="High priority safety inspection overdue",
                    created_at=now - timedelta(days=10),
                    updated_at=now
                )
                m3 = MaintenanceRecord(
                    maintenance_id="MNT-2003",
                    vehicle_id=v3.id,
                    category="General Inspection",
                    description="Comprehensive 50-point safety and electrical system audit",
                    scheduled_date=now - timedelta(days=7),
                    service_date=now - timedelta(days=6),
                    status="Completed",
                    priority="Low",
                    cost=3200.0,
                    mileage=21500.0,
                    service_center="Apex Vehicle Diagnostics",
                    notes="All diagnostics passed without faults",
                    created_at=now - timedelta(days=12),
                    updated_at=now - timedelta(days=6)
                )
                m4 = MaintenanceRecord(
                    maintenance_id="MNT-2004",
                    vehicle_id=v1.id,
                    category="Tire Replacement",
                    description="Drive-axle radial tire rotation and tread depth calibration",
                    scheduled_date=now + timedelta(hours=18),
                    status="Scheduled",
                    priority="High",
                    cost=16500.0,
                    mileage=33000.0,
                    service_center="Goodyear Commercial Hub",
                    notes="Scheduled during scheduled fleet maintenance window",
                    created_at=now - timedelta(days=2),
                    updated_at=now
                )

                db.add_all([m1, m2, m3, m4])
                db.commit()

                # Add initial audit history
                h1 = MaintenanceHistory(
                    maintenance_id=m1.id,
                    vehicle_id=v1.id,
                    event_type="Service Scheduled",
                    previous_status=None,
                    new_status="Scheduled",
                    cost=4500.0,
                    notes="Routine preventative maintenance created.",
                    created_at=now - timedelta(days=5)
                )
                h2 = MaintenanceHistory(
                    maintenance_id=m2.id,
                    vehicle_id=v2.id,
                    event_type="Overdue Flagged",
                    previous_status="Scheduled",
                    new_status="Overdue",
                    cost=8200.0,
                    notes="Scheduled date elapsed without technician dispatch.",
                    created_at=now - timedelta(days=2)
                )
                h3 = MaintenanceHistory(
                    maintenance_id=m3.id,
                    vehicle_id=v3.id,
                    event_type="Service Completed",
                    previous_status="In Progress",
                    new_status="Completed",
                    cost=3200.0,
                    notes="Signed off by lead mechanic.",
                    created_at=now - timedelta(days=6)
                )
                db.add_all([h1, h2, h3])
                db.commit()

    finally:
        db.close()