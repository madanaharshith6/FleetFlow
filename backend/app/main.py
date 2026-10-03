import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine, SessionLocal
from .models import User, Driver, Vehicle, Shipment
from .auth import hash_password
from .routers import auth, drivers, vehicles, dashboard, shipments, trips, routes, tracking, websockets

app = FastAPI(
    title="FleetFlow API – Fleet Management & Logistics Tracking Platform",
    description="Milestone 2: Shipment Tracking & Route Optimization Engine",
    version="2.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        os.getenv("FRONTEND_URL", "")
    ],
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


@app.get("/")
def root():
    return {
        "message": "FleetFlow Logistics & Fleet Management API",
        "version": "2.0.0",
        "milestone": 2,
        "features": [
            "Real-Time Shipment Tracking",
            "Route Optimization & Traffic Planning",
            "ETA Calculation Engine",
            "Trip Scheduling",
            "WebSocket Telemetry Stream",
            "Role-Based Access Control"
        ]
    }


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Seed demo user accounts for all 4 RBAC roles
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

        # Seed initial demo shipment if none exists
        if db.query(Shipment).count() == 0:
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
                    traffic_level="Moderate"
                )
            )
            db.commit()

    finally:
        db.close()