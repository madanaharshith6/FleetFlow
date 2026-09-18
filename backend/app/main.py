import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine, SessionLocal
from .models import User
from .auth import hash_password
from .routers import auth, drivers, vehicles, dashboard


app = FastAPI(
    title="FleetFlow API",
    version="1.0.0"
)


# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        os.getenv("FRONTEND_URL", "")
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# API routers
app.include_router(auth.router)
app.include_router(drivers.router)
app.include_router(vehicles.router)
app.include_router(dashboard.router)


# Root endpoint
@app.get("/")
def root():
    return {
        "message": "FleetFlow API is running",
        "milestone": 1
    }


# Startup configuration
@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # Find the default administrator account
        admin = db.query(User).filter(
            User.email == "admin@fleetflow.com"
        ).first()

        if admin:
            # Reset the demo administrator account
            admin.password_hash = hash_password("Admin@123")
            admin.role = "Administrator"
            admin.is_active = True

        else:
            # Create the default administrator account
            db.add(
                User(
                    email="admin@fleetflow.com",
                    password_hash=hash_password("Admin@123"),
                    role="Administrator",
                    is_active=True
                )
            )

        db.commit()

    finally:
        db.close()