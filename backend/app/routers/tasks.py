import uuid
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from ..auth import roles
from ..models import User
from ..tasks.maintenance_tasks import (
    check_overdue_maintenance_task,
    send_maintenance_reminders_task,
    aggregate_fleet_analytics_task
)
from ..celery_app import celery_app

logger = logging.getLogger("fleetflow.tasks")
router = APIRouter(prefix="/api/tasks", tags=["Celery Background Processing"])


@router.post("/maintenance-scan")
def trigger_overdue_maintenance_scan(
    user: User = Depends(roles("Administrator", "Fleet Manager"))
):
    """
    Triggers asynchronous Celery background task to scan overdue maintenance.
    Falls back gracefully if Celery broker/worker is offline.
    """
    now = datetime.utcnow()
    try:
        # Attempt to queue via Celery
        task = check_overdue_maintenance_task.delay()
        return {
            "task_id": task.id,
            "task_name": "check_overdue_maintenance_task",
            "status": "QUEUED",
            "message": "Overdue maintenance scan queued to Celery background worker via Redis",
            "timestamp": now
        }
    except Exception as e:
        logger.warning(f"Celery queue error (executing synchronously): {e}")
        # Synchronous fallback execution ensures demo never fails
        result = check_overdue_maintenance_task()
        return {
            "task_id": f"sync-{uuid.uuid4().hex[:8]}",
            "task_name": "check_overdue_maintenance_task",
            "status": "EXECUTED_DIRECT",
            "message": f"Executed maintenance scan directly (broker fallback): {result.get('flagged_count', 0)} flagged",
            "result": result,
            "timestamp": now
        }


@router.post("/maintenance-reminders")
def trigger_maintenance_reminders(
    user: User = Depends(roles("Administrator", "Fleet Manager"))
):
    """
    Triggers Celery background task to generate upcoming maintenance reminders.
    """
    now = datetime.utcnow()
    try:
        task = send_maintenance_reminders_task.delay()
        return {
            "task_id": task.id,
            "task_name": "send_maintenance_reminders_task",
            "status": "QUEUED",
            "message": "Maintenance reminder processing dispatched to Celery background worker",
            "timestamp": now
        }
    except Exception as e:
        logger.warning(f"Celery queue error (executing synchronously): {e}")
        result = send_maintenance_reminders_task()
        return {
            "task_id": f"sync-{uuid.uuid4().hex[:8]}",
            "task_name": "send_maintenance_reminders_task",
            "status": "EXECUTED_DIRECT",
            "message": f"Processed reminders directly (broker fallback): {result.get('reminders_count', 0)} prepared",
            "result": result,
            "timestamp": now
        }


@router.post("/analytics-aggregation")
def trigger_analytics_aggregation(
    user: User = Depends(roles("Administrator", "Fleet Manager"))
):
    """
    Triggers Celery background task to aggregate fleet analytics metrics.
    """
    now = datetime.utcnow()
    try:
        task = aggregate_fleet_analytics_task.delay()
        return {
            "task_id": task.id,
            "task_name": "aggregate_fleet_analytics_task",
            "status": "QUEUED",
            "message": "Fleet analytics aggregation dispatched to Celery worker",
            "timestamp": now
        }
    except Exception as e:
        logger.warning(f"Celery queue error (executing synchronously): {e}")
        result = aggregate_fleet_analytics_task()
        return {
            "task_id": f"sync-{uuid.uuid4().hex[:8]}",
            "task_name": "aggregate_fleet_analytics_task",
            "status": "EXECUTED_DIRECT",
            "message": "Aggregated fleet metrics directly (broker fallback)",
            "result": result,
            "timestamp": now
        }


@router.get("/{task_id}/status")
def get_task_status(
    task_id: str,
    user: User = Depends(roles("Administrator", "Fleet Manager", "Dispatcher"))
):
    """
    Inspects Celery AsyncResult status.
    """
    if task_id.startswith("sync-"):
        return {
            "task_id": task_id,
            "status": "SUCCESS",
            "result": "Direct synchronous execution completed"
        }

    try:
        res = celery_app.AsyncResult(task_id)
        return {
            "task_id": task_id,
            "status": res.status,
            "ready": res.ready(),
            "result": res.result if res.ready() else None
        }
    except Exception as e:
        return {
            "task_id": task_id,
            "status": "UNKNOWN",
            "error": str(e)
        }
