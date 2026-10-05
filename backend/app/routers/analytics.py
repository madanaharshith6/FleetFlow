from datetime import datetime
from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..auth import roles
from ..database import get_db
from ..models import Vehicle, Driver, Shipment, Trip, MaintenanceRecord, User
from ..services.route_optimizer import FUEL_CONSUMPTION_KM_PER_LITER

router = APIRouter(prefix="/api/analytics", tags=["Operational Analytics & Fuel Monitoring"])

BENCHMARK_DIESEL_PRICE_PER_LITER = 95.00  # INR benchmark


# ========================================================
# OPERATIONAL ANALYTICS
# ========================================================

@router.get("/operational")
def get_operational_analytics(
    db: Session = Depends(get_db),
    user: User = Depends(roles("Administrator", "Fleet Manager", "Dispatcher", "Driver"))
):
    now = datetime.utcnow()

    # 1. Fleet KPIs
    total_vehicles = db.query(Vehicle).count()
    active_vehicles = db.query(Vehicle).filter(Vehicle.current_status == "Active").count()
    available_vehicles = db.query(Vehicle).filter(Vehicle.current_status == "Available").count()
    maint_vehicles = db.query(Vehicle).filter(Vehicle.current_status == "Maintenance").count()
    inactive_vehicles = total_vehicles - (active_vehicles + available_vehicles + maint_vehicles)
    inactive_vehicles = max(inactive_vehicles, 0)

    utilization_pct = round((active_vehicles / total_vehicles * 100), 1) if total_vehicles > 0 else 0.0

    # 2. Driver KPIs
    total_drivers = db.query(Driver).count()
    active_drivers = db.query(Driver).filter(Driver.is_active == True).count()
    assigned_drivers = sum(1 for d in db.query(Driver).all() if len(d.vehicles) > 0)
    unassigned_drivers = max(total_drivers - assigned_drivers, 0)

    all_drivers = db.query(Driver).all()
    avg_att = round(sum(d.attendance for d in all_drivers) / len(all_drivers), 1) if all_drivers else 100.0
    avg_perf = round(sum(d.performance for d in all_drivers) / len(all_drivers), 1) if all_drivers else 0.0

    # 3. Shipment KPIs
    total_shipments = db.query(Shipment).count()
    delivered_shipments = db.query(Shipment).filter(Shipment.status == "Delivered").count()
    delayed_shipments = db.query(Shipment).filter(Shipment.status == "Delayed").count()
    cancelled_shipments = db.query(Shipment).filter(Shipment.status == "Cancelled").count()
    active_shipments = db.query(Shipment).filter(Shipment.status.in_(["Created", "Assigned", "In Transit", "Delayed"])).count()

    completion_rate = round((delivered_shipments / total_shipments * 100), 1) if total_shipments > 0 else 0.0

    # 4. Trip KPIs
    total_trips = db.query(Trip).count()
    scheduled_trips = db.query(Trip).filter(Trip.trip_status == "Scheduled").count()
    in_transit_trips = db.query(Trip).filter(Trip.trip_status.in_(["Started", "In Transit"])).count()
    completed_trips = db.query(Trip).filter(Trip.trip_status == "Completed").count()

    # 5. Maintenance KPIs
    all_maintenance = db.query(MaintenanceRecord).all()
    total_maint = len(all_maintenance)
    scheduled_maint = sum(1 for m in all_maintenance if m.status == "Scheduled" and m.scheduled_date >= now)
    in_prog_maint = sum(1 for m in all_maintenance if m.status == "In Progress")
    completed_maint = sum(1 for m in all_maintenance if m.status == "Completed")
    overdue_maint = sum(1 for m in all_maintenance if m.status == "Overdue" or (m.status in ["Scheduled", "In Progress"] and m.scheduled_date < now))
    total_maint_cost = round(sum(m.cost for m in all_maintenance if m.cost), 2)

    return {
        "fleet": {
            "total_vehicles": total_vehicles,
            "active_vehicles": active_vehicles,
            "available_vehicles": available_vehicles,
            "maintenance_vehicles": maint_vehicles,
            "inactive_vehicles": inactive_vehicles,
            "fleet_utilization_percent": utilization_pct,
            "utilization_formula": "Fleet Utilization = (Active Vehicles / Total Fleet) * 100"
        },
        "drivers": {
            "total_drivers": total_drivers,
            "active_drivers": active_drivers,
            "assigned_drivers": assigned_drivers,
            "unassigned_drivers": unassigned_drivers,
            "average_attendance": avg_att,
            "average_performance": avg_perf
        },
        "shipments": {
            "total_shipments": total_shipments,
            "active_shipments": active_shipments,
            "delivered_shipments": delivered_shipments,
            "delayed_shipments": delayed_shipments,
            "cancelled_shipments": cancelled_shipments,
            "completion_rate_percent": completion_rate
        },
        "trips": {
            "total_trips": total_trips,
            "scheduled_trips": scheduled_trips,
            "in_transit_trips": in_transit_trips,
            "completed_trips": completed_trips
        },
        "maintenance": {
            "total_records": total_maint,
            "scheduled_records": scheduled_maint,
            "in_progress_records": in_prog_maint,
            "completed_records": completed_maint,
            "overdue_records": overdue_maint,
            "total_expenditure": total_maint_cost
        },
        "generated_at": now.isoformat()
    }


# ========================================================
# FLEET UTILIZATION
# ========================================================

@router.get("/fleet-utilization")
def get_fleet_utilization(
    db: Session = Depends(get_db),
    user: User = Depends(roles("Administrator", "Fleet Manager", "Dispatcher", "Driver"))
):
    total = db.query(Vehicle).count()
    active = db.query(Vehicle).filter(Vehicle.current_status == "Active").count()
    available = db.query(Vehicle).filter(Vehicle.current_status == "Available").count()
    maintenance = db.query(Vehicle).filter(Vehicle.current_status == "Maintenance").count()
    inactive = max(total - (active + available + maintenance), 0)

    rate = round((active / total * 100), 1) if total > 0 else 0.0

    return {
        "total_vehicles": total,
        "active_vehicles": active,
        "available_vehicles": available,
        "maintenance_vehicles": maintenance,
        "inactive_vehicles": inactive,
        "utilization_rate_percent": rate,
        "fleet_utilization_percent": rate,
        "formula": "Fleet Utilization Rate = (Active Operating Vehicles / Total Fleet Count) * 100",
        "documentation": "Active vehicles represent assets currently in transit or assigned to ongoing commercial deliveries. Available vehicles are staged at depots ready for dispatch.",
        "status_distribution": {
            "Active": active,
            "Available": available,
            "Maintenance": maintenance,
            "Inactive": inactive
        }
    }


# ========================================================
# FUEL MONITORING ANALYTICS
# ========================================================

@router.get("/fuel-monitoring")
def get_fuel_monitoring_analytics(
    db: Session = Depends(get_db),
    user: User = Depends(roles("Administrator", "Fleet Manager", "Dispatcher", "Driver"))
):
    """
    Milestone 3 Fuel Monitoring Analytics:
    Calculates fuel consumption, fuel costs, and efficiency per vehicle and corridor.
    Clearly labeled algorithmic estimation based on real trip distance and vehicle powertrain profiles.
    """
    trips = db.query(Trip).all()
    vehicles = db.query(Vehicle).all()

    total_dist = sum(t.distance_km for t in trips if t.distance_km)
    # Also include shipments with distance if no trips
    if total_dist == 0:
        total_dist = sum(s.distance_km for s in db.query(Shipment).all() if s.distance_km)

    total_fuel_liters = 0.0
    vehicle_stats: Dict[int, Dict[str, Any]] = {}

    for v in vehicles:
        efficiency = FUEL_CONSUMPTION_KM_PER_LITER.get(v.vehicle_type, 4.5)
        # Find trips for this vehicle
        v_trips = [t for t in trips if t.vehicle_id == v.id]
        v_dist = sum(t.distance_km for t in v_trips if t.distance_km)
        
        # If no explicit trips logged yet, check assigned shipments
        if v_dist == 0:
            v_shipments = [s for s in db.query(Shipment).filter(Shipment.vehicle_id == v.id).all()]
            v_dist = sum(s.distance_km for s in v_shipments if s.distance_km)
            v_trips_count = len(v_shipments)
        else:
            v_trips_count = len(v_trips)

        v_fuel = round(v_dist / efficiency, 1) if efficiency > 0 else 0.0
        v_cost = round(v_fuel * BENCHMARK_DIESEL_PRICE_PER_LITER, 2)
        total_fuel_liters += v_fuel

        vehicle_stats[v.id] = {
            "vehicle_id": v.vehicle_id,
            "registration": v.registration_number,
            "vehicle_type": v.vehicle_type,
            "trips_completed": v_trips_count,
            "total_distance_km": round(v_dist, 1),
            "estimated_fuel_liters": v_fuel,
            "fuel_efficiency_kpl": efficiency,
            "estimated_fuel_cost": v_cost
        }

    total_fuel_cost = round(total_fuel_liters * BENCHMARK_DIESEL_PRICE_PER_LITER, 2)
    avg_efficiency = round(total_dist / total_fuel_liters, 1) if total_fuel_liters > 0 else 4.8

    # Group fuel by vehicle type
    fuel_by_type: Dict[str, Dict[str, float]] = {}
    for v_data in vehicle_stats.values():
        v_type = v_data["vehicle_type"]
        if v_type not in fuel_by_type:
            fuel_by_type[v_type] = {"distance_km": 0.0, "fuel_liters": 0.0, "cost": 0.0, "efficiency_kpl": v_data["fuel_efficiency_kpl"]}
        fuel_by_type[v_type]["distance_km"] += v_data["total_distance_km"]
        fuel_by_type[v_type]["fuel_liters"] += v_data["estimated_fuel_liters"]
        fuel_by_type[v_type]["cost"] += v_data["estimated_fuel_cost"]

    # Top consuming vehicle rankings
    rankings = sorted(vehicle_stats.values(), key=lambda x: x["estimated_fuel_liters"], reverse=True)

    # Corridor breakdown
    corridor_data: Dict[str, Dict[str, Any]] = {}
    for t in trips:
        corridor = f"{t.origin} → {t.destination}"
        if corridor not in corridor_data:
            corridor_data[corridor] = {"trips": 0, "total_km": 0.0, "estimated_fuel_liters": 0.0, "estimated_cost": 0.0}
        v_eff = 4.5
        if t.vehicle:
            v_eff = FUEL_CONSUMPTION_KM_PER_LITER.get(t.vehicle.vehicle_type, 4.5)
        dist = t.distance_km or 0.0
        fuel = dist / v_eff
        corridor_data[corridor]["trips"] += 1
        corridor_data[corridor]["total_km"] += dist
        corridor_data[corridor]["estimated_fuel_liters"] += fuel
        corridor_data[corridor]["estimated_cost"] += (fuel * BENCHMARK_DIESEL_PRICE_PER_LITER)

    corridor_list = [
        {
            "corridor": k,
            "trips": v["trips"],
            "total_km": round(v["total_km"], 1),
            "estimated_fuel_liters": round(v["estimated_fuel_liters"], 1),
            "estimated_cost": round(v["estimated_cost"], 2)
        }
        for k, v in corridor_data.items()
    ]

    return {
        "total_distance_logged_km": round(total_dist, 1),
        "total_fuel_consumed_liters": round(total_fuel_liters, 1),
        "total_fuel_cost_estimated": total_fuel_cost,
        "average_fleet_efficiency_kpl": avg_efficiency,
        "fuel_by_vehicle_type": fuel_by_type,
        "vehicle_rankings": rankings[:8],
        "corridor_fuel_breakdown": corridor_list,
        "methodology": "Algorithmic Estimation: Fuel consumption is accurately computed from real persisted trip distances mapped against standardized commercial powertrain profiles (Truck: 4.5 km/L, Container: 3.8 km/L, Van: 10.5 km/L) and commercial benchmark diesel rates (₹95.00/L). No physical OBD-II / CAN-bus hardware is connected; values represent accurate algorithmic fleet estimation."
    }
