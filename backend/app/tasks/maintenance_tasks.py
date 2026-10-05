import logging
from datetime import datetime, timedelta
from ..celery_app import celery_app
from ..database import SessionLocal
from ..models import MaintenanceRecord, MaintenanceHistory, Vehicle, Trip

logger = logging.getLogger("fleetflow.celery")


@celery_app.task(name="app.tasks.maintenance_tasks.check_overdue_maintenance_task")
def check_overdue_maintenance_task():
    """
    Background worker job:
    Scans maintenance schedules and flags overdue services.
    Idempotent and safely logged.
    """
    db = SessionLocal()
    now = datetime.utcnow()
    flagged_count = 0
    try:
        # Find scheduled services that are past their due date
        overdue_candidates = db.query(MaintenanceRecord).filter(
            MaintenanceRecord.status == "Scheduled",
            MaintenanceRecord.scheduled_date < now
        ).all()

        for record in overdue_candidates:
            record.status = "Overdue"
            record.updated_at = now

            # Audit into history
            history = MaintenanceHistory(
                maintenance_id=record.id,
                vehicle_id=record.vehicle_id,
                event_type="Overdue Flagged by Celery Worker",
                previous_status="Scheduled",
                new_status="Overdue",
                cost=record.cost,
                notes=f"Service scheduled for {record.scheduled_date.strftime('%Y-%m-%d')} has elapsed without completion.",
                created_at=now
            )
            db.add(history)
            flagged_count += 1

        db.commit()
        logger.info(f"[Celery] check_overdue_maintenance_task completed. Flagged {flagged_count} records as Overdue.")
        return {
            "status": "success",
            "flagged_count": flagged_count,
            "checked_at": now.isoformat()
        }
    except Exception as e:
        db.rollback()
        logger.error(f"[Celery] check_overdue_maintenance_task failed: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


@celery_app.task(name="app.tasks.maintenance_tasks.send_maintenance_reminders_task")
def send_maintenance_reminders_task():
    """
    Background worker job:
    Scans upcoming maintenance due within the next 48 hours and prepares reminders.
    """
    db = SessionLocal()
    now = datetime.utcnow()
    reminder_window = now + timedelta(days=2)
    try:
        upcoming = db.query(MaintenanceRecord).filter(
            MaintenanceRecord.status == "Scheduled",
            MaintenanceRecord.scheduled_date >= now,
            MaintenanceRecord.scheduled_date <= reminder_window
        ).all()

        reminders = []
        for r in upcoming:
            v_code = r.vehicle.vehicle_id if r.vehicle else "N/A"
            reg = r.vehicle.registration_number if r.vehicle else "N/A"
            reminders.append({
                "maintenance_id": r.maintenance_id,
                "vehicle": f"{v_code} ({reg})",
                "category": r.category,
                "scheduled_date": r.scheduled_date.isoformat(),
                "priority": r.priority
            })

        logger.info(f"[Celery] send_maintenance_reminders_task completed. Prepared {len(reminders)} reminders.")
        return {
            "status": "success",
            "reminders_count": len(reminders),
            "reminders": reminders,
            "checked_at": now.isoformat()
        }
    except Exception as e:
        logger.error(f"[Celery] send_maintenance_reminders_task failed: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


@celery_app.task(name="app.tasks.maintenance_tasks.aggregate_fleet_analytics_task")
def aggregate_fleet_analytics_task():
    """
    Background worker job:
    Aggregates fleet performance, maintenance costs, and trip metrics.
    """
    db = SessionLocal()
    now = datetime.utcnow()
    try:
        total_vehicles = db.query(Vehicle).count()
        active_vehicles = db.query(Vehicle).filter(Vehicle.current_status == "Active").count()
        maintenance_vehicles = db.query(Vehicle).filter(Vehicle.current_status == "Maintenance").count()
        available_vehicles = db.query(Vehicle).filter(Vehicle.current_status == "Available").count()

        total_maintenance_cost = sum(r.cost for r in db.query(MaintenanceRecord).all())
        completed_trips = db.query(Trip).filter(Trip.trip_status == "Completed").count()

        utilization_rate = round((active_vehicles / total_vehicles * 100), 1) if total_vehicles > 0 else 0.0

        summary = {
            "total_vehicles": total_vehicles,
            "active_vehicles": active_vehicles,
            "maintenance_vehicles": maintenance_vehicles,
            "available_vehicles": available_vehicles,
            "fleet_utilization_percent": utilization_rate,
            "total_maintenance_cost": round(total_maintenance_cost, 2),
            "completed_trips": completed_trips,
            "aggregated_at": now.isoformat()
        }
        logger.info(f"[Celery] aggregate_fleet_analytics_task completed: {summary}")
        return {"status": "success", "analytics": summary}
    except Exception as e:
        logger.error(f"[Celery] aggregate_fleet_analytics_task failed: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()
