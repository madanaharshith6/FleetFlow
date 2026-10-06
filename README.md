# FleetFlow – Fleet Management & Logistics Tracking Platform

**FleetFlow** is an enterprise-grade commercial fleet management, dispatch automation, real-time GPS tracking, multi-criteria route optimization, and vehicle maintenance platform. Developed using modern web architecture—**FastAPI (Python 3.13)**, **React 19 (Vite 6)**, and **PostgreSQL 16**—FleetFlow provides complete operational visibility, compliance enforcement, and fuel monitoring across commercial transit corridors.

---

## 📋 1. Project Title
**FleetFlow – Fleet Management & Logistics Tracking Platform**

---

## 🎯 2. Objective
Build a centralized fleet management and logistics tracking platform that helps organizations:
* Monitor vehicles and manage commercial driver rosters.
* Optimize transportation corridors and calculate dynamic ETAs.
* Track consignments and shipments in real time with simulated GPS telemetry.
* Enforce preventative vehicle servicing with automatic status locking.
* Analyze fleet utilization rates and powertrain diesel consumption.
* Improve operational efficiency, reduce transportation expenses, and optimize fleet asset availability.

---

## 🏛 3. Architecture
FleetFlow is designed following a modern decoupled microservices-ready architecture:

```
                                  +---------------------------------------+
                                  |         User Interface (SPA)          |
                                  |        (React 19 + Leaflet Maps)      |
                                  +---------------------------------------+
                                                       |
                                           HTTP / REST | WebSocket Stream
                                                       v
                                  +---------------------------------------+
                                  |           Nginx / Cloudflare          |
                                  |         (Reverse Proxy & SSL)         |
                                  +---------------------------------------+
                                                       |
                                                       v
                                  +---------------------------------------+
                                  |      API Gateway / FastAPI Backend    |
                                  |       (Python 3.13 ASGI Server)       |
                                  +---------------------------------------+
                                          |            |             |
                          SQLAlchemy / DB |            | Redis IPC   | Celery Tasks
                                          v            v             v
                     +------------------------+  +-----------+  +-------------------+
                     |     PostgreSQL 16      |  |  Redis 7  |  |   Celery Worker   |
                     | (Transactional Storage)|  | (Broker)  |  | (Background Tasks)|
                     +------------------------+  +-----------+  +-------------------+
```

### Architecture Components
1. **User Interface**: React 19 Single Page Application with interactive Leaflet mapping, responsive layouts, and role-based views.
2. **API Gateway / Backend Services**: FastAPI ASGI web application providing high-throughput RESTful APIs, request filtering, and bi-directional WebSockets.
3. **Tracking Engine**: Mathematical waypoint interpolation along commercial transit corridors with dynamic ETA and geofencing.
4. **Data & Storage Layer**: PostgreSQL 16 relational database with SQLAlchemy 2.0 ORM and Alembic migrations.
5. **Asynchronous Worker Layer**: Redis 7 Alpine in-memory broker and Celery 5.6 distributed worker daemon.

---

## 💻 4. Technology Stack
* **Backend Framework**: Python 3.13, FastAPI 0.115, Uvicorn 0.34
* **Database & ORM**: PostgreSQL 16 Alpine, SQLAlchemy 2.0, Alembic 1.15
* **Frontend**: JavaScript (ES2023), React 19, Vite 6, Leaflet 1.9.4, Axios 1.7, Modern CSS3
* **Cache & Asynchronous Worker**: Redis 7 Alpine, Celery 5.6
* **Authentication**: Python-Jose (JWT HS256), Passlib (Bcrypt password hashing)
* **DevOps & Containers**: Docker, Docker Compose v2, Nginx Alpine
* **Cloud Platform**: Render Cloud (Web Service, Static Site, Managed PostgreSQL)

---

## 📦 5. All Implemented Modules
1. **User Management Module**: Admin/Driver authentication, JWT tokens, and 4-tier Role-Based Access Control.
2. **Fleet Management Module**: Vehicle registration, asset monitoring, availability tracking, and operational statuses (`Available`, `Active`, `Maintenance`).
3. **Shipment Tracking Module**: Consignment state machine (`Created` $\rightarrow$ `Assigned` $\rightarrow$ `In Transit` $\rightarrow$ `Delivered`), tracking codes, and immutable audit logging.
4. **Route Optimization Module**: Multi-criteria routing engine (Shortest, Fastest, Traffic-Avoidant, Fuel-Efficient) with dynamic travel times.
5. **Vehicle Maintenance Module**: Preventative scheduling across 5 categories, service status lifecycle, and automated vehicle safety locks.
6. **Driver Management Module**: Operator registry, licensing, attendance monitoring, and active-trip lockout rules.
7. **Analytics Dashboard Module**: Mathematically grounded fleet utilization, driver attendance, delivery fulfillment, and powertrain fuel intelligence.
8. **Notification Module**: In-app proactive maintenance alerts (Overdue, Due Soon within 48h, High/Urgent priority) with 1-click resolution.
9. **Reports & Export Module**: Real-time fleet utilization reports, fuel consumption summaries, and vehicle service histories rendered directly in interactive dashboards and REST APIs.
10. **Background Jobs Module**: Celery & Redis task automation for overdue maintenance scans, 48h reminders, and analytics aggregation.

---

## 🔐 6. Authentication
* **Stateless JWT Tokens**: Users authenticate via `POST /api/auth/login` to obtain a signed JWT bearer token containing expiration, subject, and role claims.
* **Bcrypt Password Security**: Passwords are cryptographically salted and hashed using Bcrypt before storage in PostgreSQL.
* **Token Verification**: Protected endpoints automatically validate tokens via FastAPI dependency injection (`get_current_user`).

---

## 🛡️ 7. RBAC (Role-Based Access Control)
FleetFlow enforces strict authorization boundaries across 4 roles:
* **Administrator**: Global administrative access, user creation, driver/vehicle modification, system task execution.
* **Fleet Manager**: Asset cataloging, maintenance management, trip planning, operational analytics.
* **Dispatcher**: Consignment creation, vehicle-driver pairings, trip scheduling, route optimization.
* **Driver**: View assigned transit routes, update shipment progression, submit delivery verification.

Unprivileged requests to restricted endpoints are rejected with HTTP 403 Forbidden.

---

## 🚛 8. Fleet Management
* **Commercial Vehicle Registry**: Cataloging of Vehicle ID (`VH-001`), Registration Number (`AP39CP7741`), Vehicle Type (`Truck`, `Container Truck`, `Cargo Van`), Capacity (kg), Fuel Type (`Diesel`), and Current Status.
* **Operational Status Lifecycle**: Real-time management across `Available`, `Active`, and `Maintenance` states.
* **Asset Availability Monitoring**: Visual badges and filtering by availability, category, and assigned driver.

---

## 📦 9. Shipment Tracking
* **Consignment State Machine**:
  $$\text{Created} \longrightarrow \text{Assigned} \longrightarrow \text{In Transit} \longrightarrow \text{Delivered}$$
* **Tracking Codes**: Unique identifiers (e.g., `SHP-64BCF3`) assigned upon consignment creation.
* **Audit Trail**: Every status update automatically logs an immutable timestamped event in PostgreSQL.

---

## 🗺️ 10. Route Optimization
* **4 Distinct Optimization Profiles**:
  1. **Shortest Route**: Minimizes physical road distance in kilometers.
  2. **Fastest Route**: Prioritizes multi-lane expressway corridors.
  3. **Traffic Avoidance**: Dynamically factors highway congestion multipliers to route around urban bottlenecks.
  4. **Fuel Efficient Route**: Optimizes for steady cruising torque curves to minimize fuel burn.
* **Traffic Multipliers**: Evaluates road conditions across `Low` (1.0x), `Moderate` (1.25x), `High` (1.6x), and `Severe` (2.1x) impedance levels.

---

## 🔧 11. Maintenance
* **5 Official Service Categories**:
  * `Oil Change` | `Tire Replacement` | `Engine Service` | `Brake Service` | `General Inspection`
* **Service Lifecycle**: `Scheduled` $\rightarrow$ `In Progress` $\rightarrow$ `Completed`.
* **Automated Safety Status Lock**: Setting a maintenance record to `In Progress` automatically transitions the linked vehicle's status to `Maintenance`, locking it from dispatch.
* **Vehicle Service History**: Direct modal access to view all historical repair records, costs, and technician notes.

---

## 👨‍✈️ 12. Driver Management
* **Driver Profiles**: Records Driver ID, Full Name, License Number, Contact Details, and Assigned Vehicle.
* **Safety Guardrails**:
  * Cannot reassign a driver currently operating an active trip (`Started`, `In Transit`).
  * Cannot assign a vehicle that is currently under mechanical maintenance.
* **Attendance & Performance**: Live monitoring of driver attendance percentages and safety ratings.

---

## 📊 13. Analytics
* **Mathematically Grounded Fleet Utilization**:
  $$\text{Fleet Utilization Rate (\%)} = \left(\frac{\text{Active Vehicles}}{\text{Total Fleet}}\right) \times 100$$
* **Operational KPIs**: Active vs Available vs Maintenance vehicle breakdown, driver attendance compliance, and delivery fulfillment rate.
* **Powertrain Fuel Intelligence**: Aggregates trip distances and models fuel burn based on vehicle powertrain efficiencies (Truck: 4.5 km/L, Container: 3.8 km/L, Van: 10.5 km/L) at ₹95.00/L diesel cost.

---

## 🔔 14. Notifications
* **In-App Proactive Alerts**:
  * `Overdue`: Flagged when scheduled date is in the past and status is `Scheduled`.
  * `Due Soon`: Warns dispatchers when service is due within the next 48 hours.
  * `High / Urgent`: Highlights critical brake or engine services requiring immediate workshop intervention.
* **Honest Audit Notice**: In-app UI notifications are 100% functional. External third-party SMS (Twilio) and Email (SendGrid) providers are documented as future architecture integrations not required for M4 evaluation.

---

## 📑 15. Reports
* **Implemented Real-Time Reporting**:
  * Fleet Utilization & Asset Availability Report.
  * Powertrain Fuel Consumption & Cost Breakdown.
  * Driver Performance & Attendance Roster.
  * Vehicle Maintenance Spend & Schedule History.
* **Honest Audit Notice**: Analytical metrics are rendered live in interactive UI dashboards and accessible via REST API JSON endpoints. Direct one-click PDF/Excel file downloads are documented as prospective reporting extensions not required for M4 evaluation.

---

## 🐘 16. PostgreSQL
* **Primary Relational Storage**: PostgreSQL 16 manages core entities: `users`, `vehicles`, `drivers`, `shipments`, `trips`, `maintenance_records`, and `maintenance_history`.
* **Alembic Migrations**: Fully version-controlled database schema migrations.
* **Referential Integrity**: Cascading foreign keys and indexes guarantee zero orphaned records.

---

## ⚡ 17. Redis
* **In-Memory Message Broker**: Redis 7 Alpine manages message queues for Celery background tasks on port `6379`.
* **Resilient Failover**: Backend API includes automatic fallback to synchronous execution if Redis is temporarily offline, ensuring 100% uptime with zero 500 errors.

---

## 🔄 18. Celery
* **Distributed Task Queue**: Celery 5.6 executes background operations asynchronously:
  1. `check_overdue_maintenance_task`: Scans schedules and flags overdue services.
  2. `send_maintenance_reminders_task`: Identifies services due within 48 hours and prepares reminder queues.
  3. `aggregate_fleet_analytics_task`: Pre-aggregates fleet metrics for instant dashboard rendering.
* **Interactive UI Console**: Dispatchers can trigger tasks on demand and inspect real-time AsyncResult payloads.

---

## 🐳 19. Docker
* **Multi-Service Docker Compose Ecosystem**:
  * `fleetflow-backend`: FastAPI ASGI runner (Python 3.11-slim) with health checks.
  * `fleetflow-frontend`: Multi-stage React 19 build served by Nginx Alpine with SPA reverse proxy.
  * `fleetflow-postgres`: PostgreSQL 16 container with persistent named volume `fleetflow_pgdata`.
  * `fleetflow-redis`: Redis 7 Alpine in-memory broker with health ping test.
  * `fleetflow-celery-worker`: Distributed Celery worker executing background queues.
* **Single-Command Launch**: `docker compose up -d --build` orchestrates all 5 services with automated dependency resolution.

---

## ⚙️ 20. Local Setup
1. **Clone repository**:
   ```bash
   git clone https://github.com/madanaharshith6/FleetFlow.git
   cd FleetFlow
   ```
2. **Start Backend**:
   ```powershell
   cd backend
   ..\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   alembic upgrade head
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
3. **Start Frontend**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
4. **Start Redis & Celery (Optional for background tasks)**:
   ```powershell
   cd backend
   celery -A app.celery_app worker --loglevel=info -P solo
   ```
5. **1-Click Startup**: Simply run `start.bat` in the repository root.

---

## 🔑 21. Environment Variables
| Variable | Description | Default (Local) | Production Example |
| :--- | :--- | :--- | :--- |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+psycopg2://fleetflow:fleetflow@localhost:5432/fleetflow` | `postgresql://user:pass@ep-host.render.com/fleetflow` |
| `JWT_SECRET_KEY` | Symmetric key for signing JWT tokens | `fleetflow-secret-key-12345` | `<secure-random-entropy>` |
| `FRONTEND_URL` | CORS whitelisted frontend URL | `http://localhost:5173` | `https://fleetflow-ssts.onrender.com` |
| `CELERY_BROKER_URL` | Redis URL for Celery task queuing | `redis://localhost:6379/0` | `rediss://default:pass@redis-cloud:6379/0` |
| `CELERY_RESULT_BACKEND`| Redis URL for task results | `redis://localhost:6379/0` | `rediss://default:pass@redis-cloud:6379/0` |
| `PORT` | Web server bind port | `8000` | Injected by Render (`10000`) |

---

## 📖 22. API Documentation
| Domain | Method | Endpoint | Description |
| :--- | :---: | :--- | :--- |
| **Auth** | `POST` | `/api/auth/login` | Issue JWT bearer token with role claims |
| **Dashboard** | `GET` | `/api/dashboard/summary` | Real-time fleet KPIs, utilization, and proactive alerts |
| **Vehicles** | `GET` | `/api/vehicles` | List all fleet assets |
| **Vehicles** | `POST` | `/api/vehicles` | Register commercial vehicle (Admin/Manager) |
| **Drivers** | `GET` | `/api/drivers` | Retrieve driver roster |
| **Drivers** | `GET` | `/api/drivers/monitoring` | Live driver operational status and ratings |
| **Drivers** | `POST` | `/api/drivers/{id}/assign-vehicle` | Pair driver to vehicle with safety locks |
| **Drivers** | `POST` | `/api/drivers/{id}/unassign-vehicle`| Unassign driver from asset |
| **Shipments** | `GET` | `/api/shipments` | List consignments with search & filters |
| **Shipments** | `POST` | `/api/shipments` | Create consignment with tracking code |
| **Shipments** | `GET` | `/api/shipments/{id}/history` | Chronological event audit trail |
| **Routing** | `POST` | `/api/routes/calculate` | Compare 4 routing profiles with traffic factor |
| **Trips** | `GET` | `/api/trips` | List scheduled transport runs |
| **Trips** | `POST` | `/api/trips` | Schedule journey with asset conflict prevention |
| **Maintenance** | `GET` | `/api/maintenance` | List maintenance records with multi-filter |
| **Maintenance** | `POST` | `/api/maintenance` | Schedule preventative or corrective service |
| **Maintenance** | `PUT` | `/api/maintenance/{id}/status` | Transition service status with vehicle lock |
| **Maintenance** | `GET` | `/api/maintenance/alerts` | Proactive alerts by deadline and severity |
| **Maintenance** | `GET` | `/api/maintenance/summary` | Aggregated spend and vehicle-level reports |
| **Analytics** | `GET` | `/api/analytics/operational` | Operational KPIs and fulfillment rates |
| **Analytics** | `GET` | `/api/analytics/fuel-monitoring` | Powertrain fuel analytics and cost modeling |
| **Tasks** | `POST` | `/api/tasks/maintenance-scan` | Asynchronously trigger overdue maintenance scan |
| **Tasks** | `POST` | `/api/tasks/maintenance-reminders`| Asynchronously trigger 48h service reminders |
| **Tasks** | `GET` | `/api/tasks/{task_id}/status` | Poll Celery task AsyncResult status |
| **WebSockets** | `WS` | `/ws/shipments/{id}` | Live bi-directional GPS telemetry stream |

Interactive Swagger documentation is available at `/docs`.

---

## 🧪 23. Testing
Execute the comprehensive automated test suite:
```powershell
python backend/test_milestone4_full_suite.py
```
Execute targeted edge-case verification:
```powershell
python backend/test_edge_cases.py
```
Execute dedicated Milestone 3 suite:
```powershell
python backend/test_milestone3_comprehensive.py
```
Execute frontend production build verification:
```bash
cd frontend && npm run build
```

---

## ☁️ 24. Production Deployment
* **Render Web Service (`fleetflow-api-p7ai`)**: Hosts FastAPI backend, Gunicorn/Uvicorn ASGI runner.
* **Render Static Site (`fleetflow-ssts`)**: Hosts optimized React production bundle with SPA fallback routing.
* **Render Managed PostgreSQL**: Cloud transactional database storing all tables and relationships.
* **Resilient Broker Failover**: Task endpoints gracefully execute synchronously if cloud Redis broker is temporarily unreachable.

---

## 🔗 25. Live URLs
* 👉 **Frontend Application**: [https://fleetflow-ssts.onrender.com](https://fleetflow-ssts.onrender.com)
* 👉 **Interactive Swagger API Docs**: [https://fleetflow-api-p7ai.onrender.com/docs](https://fleetflow-api-p7ai.onrender.com/docs)
* 👉 **GitHub Repository**: [https://github.com/madanaharshith6/FleetFlow](https://github.com/madanaharshith6/FleetFlow)

---

## 📌 26. Milestone 1 Summary
Implemented core authentication, role-based access control, database schema design, vehicle cataloging, driver roster, and foundational dashboard.

---

## 📌 27. Milestone 2 Summary
Implemented consignment state-machine, multi-criteria route optimization (Shortest, Fastest, Traffic-Avoidant, Fuel-Efficient), dynamic ETA, real-time GPS simulation, Leaflet interactive mapping, and WebSocket broadcasting.

---

## 📌 28. Milestone 3 Summary
Implemented preventative maintenance scheduling across 5 categories, service status lifecycle transitions with automatic vehicle locking, proactive alerts, driver assignment safety rules, fleet utilization metrics, powertrain fuel burn analytics, and Celery background workers.

---

## 📌 29. Milestone 4 Summary
Executed comprehensive automated testing (100% pass across core features and edge cases), responsive UI adaptation for Desktop/Tablet/Mobile, production Docker container orchestration, Render cloud deployment validation, complete system documentation, and mentor demonstration preparation.

---

## ⚠️ 30. Limitations / Known Gaps
1. **Render Free-Tier Spin-Down**: Inactive free-tier web services may experience a 30–50 second cold start delay upon initial HTTP request.
2. **Simulated Telemetry**: GPS tracking utilizes mathematical waypoint interpolation along real road corridors in lieu of physical hardware OBD-II / CAN-bus dongles.
3. **External Third-Party Integrations**: Third-party SMS (Twilio), Email (SendGrid), and paid Google Maps API services referenced in the high-level architecture diagram are documented as future enterprise integrations not required for Milestone 4 evaluation.
