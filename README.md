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

### Milestone 3: Maintenance Management & Analytics
* **Vehicle Maintenance Management Module**:
  * Formal preventative and corrective servicing cataloging across 5 standardized categories:
    * `Oil Change`
    * `Tire Replacement`
    * `Engine Service`
    * `Brake Service`
    * `General Inspection`
  * Complete lifecycle state transitions: `Scheduled` $\longrightarrow$ `In Progress` $\longrightarrow$ `Completed` (or `Overdue` / `Cancelled`).
  * Automatic synchronization with vehicle asset state: moving a vehicle into `In Progress` maintenance automatically locks its operational status to `Maintenance` in the database, preventing accidental dispatch.
  * Multi-record audit trail per service and historical service lookup per vehicle asset.
* **Proactive Maintenance Alerts**:
  * Real-time telemetry evaluating scheduled dates, priority levels (`Urgent`, `High`, `Medium`, `Low`), and overdue elapsed periods.
  * Visual severity classifications: `critical` (overdue or urgent), `warning` (due within 48h or high priority), and `info`.
* **Driver Assignment System & Operational Monitoring**:
  * Driver-to-vehicle pairing system with rigorous business rule validation: prevents assigning drivers to vehicles currently tagged in `Maintenance`.
  * Operational roster tracking driver attendance %, performance rating (out of 5.0), and dispatch state (`Available`, `Assigned`, `On Trip`).
  * One-click vehicle assignment and release actions with instant PostgreSQL persistence.
* **Fleet Performance & Operational Analytics**:
  * Transparently grounded formulas for key fleet metrics:
    $$\text{Fleet Utilization Rate (\%)} = \left(\frac{\text{Active Operating Vehicles}}{\text{Total Fleet Count}}\right) \times 100$$
  * Metric breakdowns for asset availability, attendance compliance, fulfillment completion rates, and dispatched trips.
* **Powertrain Fuel Monitoring & Cost Analytics**:
  * Trip distance aggregation mapped against powertrain consumption benchmarks:
    * Container Truck: $3.8\text{ km/L}$
    * Commercial Truck: $4.5\text{ km/L}$
    * Light Cargo Van: $10.5\text{ km/L}$
  * Accurate diesel burn estimation and financial expenditure modeling based on Indian commercial diesel pricing ($\approx ₹95.00/\text{L}$).
* **Celery Asynchronous Background Processing with Redis**:
  * Distributed asynchronous task worker architecture running with Redis message broker and result backend.
  * Configured background tasks:
    1. `check_overdue_maintenance_task`: Scans database for elapsed schedules and transitions records to `Overdue`.
    2. `send_maintenance_reminders_task`: Identifies services due within 48 hours and dispatches proactive notifications.
    3. `aggregate_fleet_analytics_task`: Pre-aggregates fleet utilization and operational spend metrics for instant dashboard delivery.
  * RESTful task execution trigger endpoints with polling support for task `PENDING` and `SUCCESS` states.

---

## 🛠 Technology Stack

* **Frontend**: React 19, Vite 6, JavaScript (ESM), Axios, Leaflet (OpenStreetMap), Modern CSS.
* **Backend**: Python 3.13, FastAPI 0.115, Uvicorn, Celery 5.6, SQLAlchemy 2.0, Pydantic v2, Python-Jose (JWT), Passlib (Bcrypt), WebSockets.
* **Database**: PostgreSQL 16 (Dockerized container: `fleetflow-postgres`).
* **Message Broker & Task Backend**: Redis 7 Alpine (Dockerized container: `fleetflow-redis`).
* **Schema Migrations**: Alembic 1.15.

---

### 📦 Project Structure

```
D:\Harshith
├── backend
│   ├── alembic/              # Database migration versions
│   │   └── versions/         # Alembic migration scripts (including Milestone 3 models)
│   ├── app/
│   │   ├── routers/          # API Routers (auth, dashboard, drivers, routes, shipments, tracking, trips, vehicles, websockets, maintenance, analytics, tasks)
│   │   ├── services/         # Domain engines (route_optimizer.py, tracking_service.py, websocket_manager.py)
│   │   ├── tasks/            # Celery background workers (maintenance_tasks.py)
│   │   ├── celery_app.py     # Celery worker initialization & Redis broker configuration
│   │   ├── auth.py           # JWT generation, password hashing & RBAC dependencies
│   │   ├── database.py       # SQLAlchemy engine & session dependency
│   │   ├── main.py           # FastAPI application & startup seed data
│   │   ├── models.py         # PostgreSQL database models (Vehicles, Drivers, Shipments, Trips, MaintenanceRecord, MaintenanceHistory)
│   │   └── schemas.py        # Pydantic validation schemas
│   ├── requirements.txt      # Python dependencies (FastAPI, Celery, Redis, SQLAlchemy, Alembic, etc.)
│   ├── test_milestone3_comprehensive.py # Automated test suite (100% pass)
│   └── alembic.ini           # Alembic migration configuration
├── frontend
│   ├── src/
│   │   ├── main.jsx          # Complete React 19 SPA with modern navigation, Maintenance, Analytics, and Celery HUD
│   │   └── styles.css        # Presentation-grade CSS stylesheet
│   ├── index.html            # Single page mount with Inter font & Leaflet CDN
│   ├── package.json          # Node dependencies
│   └── vite.config.js        # Vite build configuration (Port 5173)
├── docker-compose.yml        # PostgreSQL 16 & Redis 7 container orchestration
└── README.md                 # Project documentation
```

---

## ⚡ Quick Start Guide (Windows)

### 1. Start PostgreSQL & Redis (Docker)
Open PowerShell:
```powershell
cd D:\Harshith
docker compose up -d
```
Verify both containers (`fleetflow-postgres` and `fleetflow-redis`) are running healthy:
```powershell
docker ps
```

### 2. Start Backend (FastAPI)
In Terminal 1:
```powershell
cd D:\Harshith\backend
..\venv\Scripts\Activate.ps1
alembic upgrade head
uvicorn app.main:app --port 8000
```
* **API Root**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
* **Interactive Swagger Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 3. Start Celery Background Worker
In Terminal 2 (with Redis running on port 6379):
```powershell
cd D:\Harshith\backend
..\venv\Scripts\Activate.ps1
celery -A app.celery_app worker --loglevel=info -P solo
```

### 4. Start Frontend (React + Vite)
In Terminal 3:
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
| **Administrator** | `admin@fleetflow.com` | `Admin@123` | Full administrative control, all modules, Celery task triggers |
| **Fleet Manager** | `manager@fleetflow.com` | `Admin@123` | Vehicle management, maintenance scheduling, trips, routes, analytics |
| **Dispatcher** | `dispatcher@fleetflow.com` | `Admin@123` | Consignment creation, driver assignment, trip scheduling |
| **Driver** | `driver@fleetflow.com` | `Admin@123` | View assigned shipments, live telemetry updates, assigned vehicle |

---

## 📡 API Endpoints Overview

### Authentication
* `POST /api/auth/login` – Issue JWT bearer token with role claims.

### Dashboard
* `GET /api/dashboard/summary` – Real-time operational metrics, fleet utilization %, total fuel burn, and proactive alerts.

### Vehicle Maintenance Management (Milestone 3)
* `GET /api/maintenance` – List all maintenance records (supports `status`, `category`, `priority`, `vehicle_id` filters).
* `POST /api/maintenance` – Schedule new maintenance service in PostgreSQL.
* `GET /api/maintenance/{id}` – Get detailed maintenance record.
* `PUT /api/maintenance/{id}` – Update maintenance record details.
* `PUT /api/maintenance/{id}/status` – Transition status (`Scheduled`, `In Progress`, `Completed`, `Overdue`, `Cancelled`) with automatic vehicle lock.
* `DELETE /api/maintenance/{id}` – Cancel maintenance record and restore vehicle state.
* `GET /api/maintenance/{id}/history` – Chronological audit history of a specific maintenance record.
* `GET /api/maintenance/vehicle/{vehicle_id}/history` – Lifetime service history for a vehicle asset.
* `GET /api/maintenance/upcoming` – Filter upcoming scheduled services.
* `GET /api/maintenance/overdue` – Filter overdue services.
* `GET /api/maintenance/alerts` – Proactive maintenance alerts categorized by severity (`critical`, `warning`, `info`).
* `GET /api/maintenance/summary` – Aggregated statistics (counts, total expenditure, category breakdown).

### Driver Assignment & Monitoring (Milestone 3)
* `GET /api/drivers/monitoring` – Driver operational status (`Available`, `Assigned`, `On Trip`), attendance %, performance rating, and assigned assets.
* `POST /api/drivers/{id}/assign-vehicle` – Assign driver to vehicle with safety rules (rejects vehicles in `Maintenance`).
* `POST /api/drivers/{id}/unassign-vehicle` – Unassign driver from current vehicle.

### Operational & Fuel Analytics (Milestone 3)
* `GET /api/analytics/operational` – Fleet utilization breakdown, active driver attendance, delivery fulfillment rates, and dispatched trips.
* `GET /api/analytics/fleet-utilization` – Dedicated endpoint returning fleet utilization % and documented formula.
* `GET /api/analytics/fuel-monitoring` – Vehicle fuel efficiency rankings (km/L), trip-based diesel burn estimation, and financial cost.

### Celery Background Processing (Milestone 3)
* `POST /api/tasks/maintenance-scan` – Trigger asynchronous overdue maintenance scan task.
* `POST /api/tasks/maintenance-reminders` – Trigger asynchronous 48-hour service reminder notifications task.
* `POST /api/tasks/analytics-aggregation` – Trigger asynchronous fleet analytics aggregation task.
* `GET /api/tasks/{task_id}/status` – Query AsyncResult status (`PENDING`, `SUCCESS`, `FAILURE`) and payload.

### Shipments (Milestone 2)
* `GET /api/shipments` – List shipments (supports `search`, `status`, `driver_id`, `vehicle_id` filters).
* `POST /api/shipments` – Create consignment with auto-generated tracking code.
* `GET /api/shipments/{id}` – Detailed consignment profile with vehicle/driver links.
* `PUT /api/shipments/{id}/status` – Validated lifecycle state transition.
* `POST /api/shipments/{id}/assign` – Link fleet vehicle and driver.
* `GET /api/shipments/{id}/history` – Chronological audit trail.

### Live GPS Tracking & Route Optimization (Milestone 2)
* `GET /api/tracking/{id}` – Real-time telemetry, remaining distance, dynamic ETA, and GPS state.
* `POST /api/tracking/{id}/simulate-step` – Advance simulated vehicle along corridor.
* `POST /api/routes/calculate` – Compare Shortest, Fastest, Traffic Avoidance, and Fuel Efficient routes.
* `POST /api/routes/recalculate` – Re-evaluate ETA with updated traffic conditions.
* `GET /api/trips` – List scheduled and ongoing trips.
* `POST /api/trips` – Schedule trip with asset conflict prevention.

### WebSockets
* `WS /ws/shipments/{id}` – Live bi-directional telemetry stream.
* `WS /ws/fleet` – Global fleet monitoring stream.

---

## 🎓 Mentor Demonstration Flow

1. **Sign In**: Click the `Administrator` quick-fill button on the login screen.
2. **Dashboard Overview**:
   * Inspect the upgraded KPI grid: Total Fleet, **Fleet Utilization %**, Active Drivers, Active Shipments, **Maintenance Services & Overdue Count**, and **Total Fuel Consumed (L)**.
   * Notice the **Proactive Maintenance & Fleet Alerts** banner detecting overdue services with one-click resolution.
3. **Vehicle Maintenance Management**:
   * Open the **Maintenance** tab (`🔧`).
   * View the maintenance metrics summary, categorized list, and proactive alerts.
   * Click **+ Schedule Service**: Schedule an *Engine Service* or *Brake Service* for a fleet vehicle with scheduled date, cost, and priority.
   * Update a record's status: Click **Update Status** $\longrightarrow$ change to `In Progress` $\longrightarrow$ observe how the vehicle's operational state is automatically locked to `Maintenance`.
   * Click **History 📜** to show the complete audit trail of status transitions.
4. **Driver Assignment System**:
   * Open the **Drivers** tab (`👤`).
   * Review the driver monitoring metrics: Attendance %, Performance rating, Assigned Vehicle, and Live Status (`Available`, `Assigned`, `On Trip`).
   * Click **Assign 🚛**: Try to assign a vehicle currently in `Maintenance` $\longrightarrow$ observe the system enforcement locking assignment for safety!
   * Assign an available vehicle $\longrightarrow$ observe instant pairing and status update.
5. **Operational Analytics & Fuel Monitoring**:
   * Open the **Analytics & Fuel** tab (`📈`).
   * Review the **Fleet Utilization Breakdown** with the documented formula:
     $$\text{Fleet Utilization Rate} = (\text{Active Vehicles} / \text{Total Fleet}) \times 100$$
   * Examine **Fuel Monitoring & Powertrain Consumption Rankings**: See real trip distances mapped against km/L fuel efficiency and Indian diesel cost estimation (₹95.00/L).
6. **Celery Asynchronous Worker & Redis**:
   * In the **Analytics & Fuel** page, locate the **Celery Background Worker Engine** panel.
   * Click **⚡ Trigger Overdue Maintenance Scan**: The task is dispatched to Redis and executed asynchronously by the Celery worker; the live console displays the completed task result!
   * Click **🔔 Trigger 48h Service Reminders** and **📊 Trigger Fleet Analytics Aggregation** to observe asynchronous execution in real-time.
7. **Shipments & Live Tracking (Milestone 2 Verified)**:
   * Open **Live Tracking** (`📡`) $\longrightarrow$ click **▶ Simulate Next Waypoint** $\longrightarrow$ observe real-time map updates, GPS HUD, and dynamic ETA without breaking changes.
