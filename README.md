# FleetFlow – Milestone 1 Complete

Based on the supplied FleetFlow project specification.

Implemented:
1. Project objective/workflow foundation
2. React frontend
3. FastAPI backend
4. JWT authentication
5. Role-based access control
6. PostgreSQL integration
7. Alembic migration
8. Driver management
9. Vehicle registration
10. Fleet monitoring dashboard

Milestone 2 features such as GPS shipment tracking, route optimization and WebSockets are intentionally not included yet.

## Run

### Database
    docker compose up -d db

### Backend
    cd backend
    python -m venv venv
    # Windows: venv\Scripts\activate
    # macOS/Linux: source venv/bin/activate
    pip install -r requirements.txt
    copy .env.example .env       # Windows
    # cp .env.example .env       # macOS/Linux
    alembic upgrade head
    uvicorn app.main:app --reload

API: http://127.0.0.1:8000
Swagger: http://127.0.0.1:8000/docs

### Frontend
Open another terminal:
    cd frontend
    npm install
    npm run dev

Open: http://127.0.0.1:5173

### Demo login
Email: admin@fleetflow.com
Password: Admin@123

Change the demo password/secret before real deployment.
