# FleetFlow – Fleet Management & Logistics Tracking Platform

**FleetFlow** is a centralized fleet management, shipment dispatch, real-time GPS tracking, and route optimization platform developed using **FastAPI (Python 3.13)**, **React 19**, and **PostgreSQL 16**.

Designed for commercial logistics providers, courier services, and supply chain operations to monitor vehicles, track shipments in real time, and optimize transportation corridors.

---

## 🚀 Key Modules & Milestones

### Milestone 1: Core Foundation & Fleet Operations
* **JWT Authentication & RBAC**: Secure bearer token authentication with role-based access control for 4 roles:
  * `Administrator`: Full system administration, fleet, and consignment privileges.
  * `Fleet Manager`: Vehicle registration, fleet dispatch, trip management, and route planning.
  * `Dispatcher`: Consignment creation, vehicle-driver assignment, and trip scheduling.
  * `Driver`: Assigned transit monitoring, delivery completion, and telemetry updates.
* **Fleet Management**: Commercial vehicle cataloging (Trucks, Vans, Container Trucks, Cars), capacity tracking, fuel classifications, and dynamic availability states (`Available`, `Active`, `Maintenance`).
* **Driver Roster**: Operator registration, commercial licensing, attendance metrics, and vehicle-driver assignments.
* **Fleet Monitoring Dashboard**: High-level KPI cards and asset utilization counters.
* **Database & Migrations**: PostgreSQL integration with SQLAlchemy ORM and Alembic transactional migrations.

### Milestone 2: Shipment Tracking & Route Optimization
* **End-to-End Shipment Lifecycle**: Formal state-machine transitions:
  $$\text{Created} \longrightarrow \text{Assigned} \longrightarrow \text{In Transit} \longrightarrow \text{Delivered}$$
  (with handling for `Delayed` and `Cancelled` states).
* **Multi-Objective Route Optimization Engine**: Algorithmic comparison across 4 routing profiles:
  1. **Shortest Route**: Minimizes physical kilometers traveled via direct state links.
  2. **Fastest Route**: Utilizes high-speed multi-lane National Expressway corridors.
  3. **Traffic Avoidance**: Leverages peripheral bypasses and outer ring corridors to evade urban choke-points.
  4. **Fuel Efficient Route**: Calculates steady cruising torque curves (60–70 km/h) to reduce fuel burn and $\text{CO}_2$ emissions.
* **Traffic-Aware Planning**: Models congestion dynamics (`Low`, `Moderate`, `High`, `Severe`) with travel-time multipliers and dynamic ETA recalculation.
* **Dynamic ETA Service**: Algorithmic arrival estimation based on remaining distance, transit velocity, and traffic impedance.
* **Simulated GPS Telemetry**: Real-time corridor position updates with waypoint interpolation between origin and destination hubs.
* **Interactive Map Visualization**: Embedded Leaflet & OpenStreetMap interactive mapping displaying live vehicle markers, origin/destination pins, and transit corridors without paid API keys.
* **WebSocket Real-Time Stream**: Bi-directional FastAPI WebSockets (`/ws/shipments/{id}`) broadcasting instant telemetry, status changes, and arrival alerts.
* **Trip Scheduling & Conflict Prevention**: Journey scheduling linking vehicles, drivers, and consignments, with conflict detection to prevent asset double-booking.
* **Event Audit Trail**: Chronological event logging (`Shipment Created`, `Asset Assigned`, `GPS Telemetry Update`, `Status Changed`) in PostgreSQL.

---

## 🛠 Technology Stack

* **Frontend**: React 19, Vite 6, JavaScript (ESM), Axios, Leaflet (OpenStreetMap), Modern CSS.
* **Backend**: Python 3.13, FastAPI 0.115, Uvicorn, SQLAlchemy 2.0, Pydantic v2, Python-Jose (JWT), Passlib (Bcrypt), WebSockets.
* **Database**: PostgreSQL 16 (Dockerized container: `fleetflow-postgres`).
* **Schema Migrations**: Alembic 1.15.

---

## 📦 Project Structure

```
D:\Harshith
├── backend
│   ├── alembic/              # Database migration versions
│   ├── app/
│   │   ├── routers/          # API Routers (auth, dashboard, drivers, routes, shipments, tracking, trips, vehicles, websockets)
│   │   ├── services/         # Domain engines (route_optimizer.py, tracking_service.py, websocket_manager.py)
│   │   ├── auth.py           # JWT generation, password hashing & RBAC dependencies
│   │   ├── database.py       # SQLAlchemy engine & session dependency
│   │   ├── main.py           # FastAPI application & startup seed data
│   │   ├── models.py         # PostgreSQL database models
│   │   └── schemas.py        # Pydantic validation schemas
│   ├── requirements.txt      # Python dependencies
│   └── alembic.ini           # Alembic migration configuration
├── frontend
│   ├── src/
│   │   ├── main.jsx          # Complete React 19 SPA with modern navigation & views
│   │   └── styles.css        # Presentation-grade CSS stylesheet
│   ├── index.html            # Single page mount with Inter font & Leaflet CDN
│   ├── package.json          # Node dependencies
│   └── vite.config.js        # Vite build configuration (Port 5173)
├── docker-compose.yml        # PostgreSQL 16 container definition
└── README.md                 # Project documentation
```

---

## ⚡ Quick Start Guide (Windows)

### 1. Start PostgreSQL (Docker)
Open PowerShell:
```powershell
cd D:\Harshith
docker compose up -d
```
Verify container is running:
```powershell
docker ps
```

### 2. Start Backend (FastAPI)
In Terminal 1:
```powershell
cd D:\Harshith\backend
..\venv\Scripts\Activate.ps1
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```
* **API Root**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
* **Interactive Swagger Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 3. Start Frontend (React + Vite)
In Terminal 2:
```powershell
cd D:\Harshith\frontend
npm run dev
```
Open your browser at:
👉 **[http://localhost:5173/](http://localhost:5173/)**

---

## 🔑 Demo Login Credentials

The application seeds accounts for all 4 roles automatically on startup. Use the one-click quick-fill buttons on the login screen or enter manually:

| Role | Email | Password | Allowed Permissions |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin@fleetflow.com` | `Admin@123` | Full administrative control, all modules |
| **Fleet Manager** | `manager@fleetflow.com` | `Admin@123` | Vehicle management, trips, routes, consignments |
| **Dispatcher** | `dispatcher@fleetflow.com` | `Admin@123` | Consignment creation, asset assignment, trip scheduling |
| **Driver** | `driver@fleetflow.com` | `Admin@123` | View assigned shipments, live telemetry updates |

---

## 📡 API Endpoints Overview

### Authentication
* `POST /api/auth/login` – Issue JWT bearer token with role claims.

### Dashboard
* `GET /api/dashboard/summary` – Real-time operational metrics and recent activity feed.

### Shipments
* `GET /api/shipments` – List shipments (supports `search`, `status`, `driver_id`, `vehicle_id` filters).
* `POST /api/shipments` – Create consignment with auto-generated tracking code.
* `GET /api/shipments/{id}` – Detailed consignment profile with vehicle/driver links.
* `PUT /api/shipments/{id}/status` – Validated lifecycle state transition.
* `POST /api/shipments/{id}/assign` – Link fleet vehicle and driver.
* `GET /api/shipments/{id}/history` – Chronological audit trail.

### Live GPS Tracking & Simulation
* `GET /api/tracking/{id}` – Real-time telemetry, remaining distance, dynamic ETA, and GPS state.
* `POST /api/tracking/{id}/simulate-step` – Advance simulated vehicle along corridor (for mentor presentation).
* `POST /api/tracking/{id}/location` – External or hardware GPS coordinates ingestion.

### Route Optimization
* `POST /api/routes/calculate` – Compare Shortest, Fastest, Traffic Avoidance, and Fuel Efficient routes.
* `POST /api/routes/recalculate` – Re-evaluate ETA with updated traffic conditions.

### Trip Scheduling
* `GET /api/trips` – List scheduled and ongoing trips.
* `POST /api/trips` – Schedule trip with asset conflict prevention.
* `PUT /api/trips/{id}/status` – Transition journey states (`Scheduled`, `Started`, `In Transit`, `Completed`).

### WebSockets
* `WS /ws/shipments/{id}` – Live bi-directional telemetry stream.
* `WS /ws/fleet` – Global fleet monitoring stream.

---

## 🎓 Mentor Demonstration Flow

1. **Sign In**: Click the `Administrator` quick-fill button on the login screen.
2. **Dashboard Overview**: Inspect the live KPI cards and operational feed.
3. **Route Optimization**:
   * Open the **Route Optimization** tab.
   * Enter *Vijayawada* to *Hyderabad*, select *High* traffic, and click **Optimize Corridor**.
   * Review the comparison matrix showing travel times, fuel consumption, and the *Traffic Avoidance* recommendation.
4. **Shipment Dispatch**:
   * Open the **Shipments** tab and click **+ Create Shipment**.
   * Assign a fleet vehicle and certified driver.
5. **Live GPS Tracking**:
   * Click **Track 📡** on any active shipment.
   * Observe the interactive Leaflet map with vehicle pin, coordinates, dynamic ETA, and telemetry HUD.
   * Click **▶ Simulate Next Waypoint** to watch the vehicle advance in real time along the corridor with instant telemetry and audit history updates!
6. **Audit Trail**:
   * Return to Shipments and click **History 📜** to show the chronological event log.
7. **RBAC Verification**:
   * Log out and sign in as `Driver` (`driver@fleetflow.com`).
   * Verify that vehicle registration forms are hidden or restricted with HTTP 403 enforcement.
