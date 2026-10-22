import io
import csv
from datetime import datetime
from typing import List, Tuple
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Vehicle, Driver, Shipment, Trip, MaintenanceRecord, User
from ..auth import current_user
from ..services.route_optimizer import FUEL_CONSUMPTION_KM_PER_LITER

router = APIRouter(prefix="/api/reports", tags=["Reports & Export Module"])

BENCHMARK_DIESEL_PRICE = 95.00


def build_pure_python_pdf(title: str, headers: List[str], rows: List[List[str]]) -> bytes:
    """
    Generates a valid, standards-compliant PDF-1.4 binary document in pure Python
    with zero external dependencies. Opens natively in all PDF viewers.
    """
    content_lines = [
        "BT",
        "/F1 16 Tf",
        "50 750 Td",
        f"({title}) Tj",
        "/F1 9 Tf",
        "0 -25 Td",
        f"(Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')} | FleetFlow Enterprise Logistics Platform) Tj",
        "0 -20 Td",
        "(" + " | ".join(headers[:6]) + ") Tj",
        "0 -10 Td",
        "(" + "-" * 75 + ") Tj"
    ]

    for r in rows[:35]:  # fit neatly on standard letter/A4 page
        safe_cells = [str(c).replace("(", "[").replace(")", "]") for c in r[:6]]
        row_str = " | ".join(safe_cells)
        content_lines.append("0 -15 Td")
        content_lines.append(f"({row_str}) Tj")

    content_lines.append("ET")
    stream_data = "\n".join(content_lines).encode("latin-1", "replace")
    stream_len = len(stream_data)

    objects = [
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n",
        f"4 0 obj\n<< /Length {stream_len} >>\nstream\n".encode("latin-1") + stream_data + b"\nendstream\nendobj\n",
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
    ]

    header = b"%PDF-1.4\n"
    body = b"".join(objects)

    offsets = [0]
    curr = len(header)
    for o in objects:
        offsets.append(curr)
        curr += len(o)

    xref_offset = curr
    xref = [f"xref\n0 {len(objects)+1}\n0000000000 65535 f \n".encode("latin-1")]
    for off in offsets[1:]:
        xref.append(f"{off:010d} 00000 n \n".encode("latin-1"))

    trailer = f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("latin-1")
    return header + body + b"".join(xref) + trailer


def build_csv_data(headers: List[str], rows: List[List[str]]) -> str:
    """
    Builds RFC-4180 standard CSV formatted data.
    """
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    for r in rows:
        writer.writerow(r)
    return output.getvalue()


@router.get("/export")
def export_report(
    report_type: str = Query("fleet_utilization", description="Type of report: fleet_utilization, fuel_consumption, driver_performance, delivery_performance, maintenance"),
    format: str = Query("csv", description="Format: csv or pdf"),
    db: Session = Depends(get_db),
    user: User = Depends(current_user)
):
    """
    Module 9: Reports & Export Module
    Exports real database-backed operational reports in CSV or PDF formats.
    """
    format = format.lower().strip()
    if format not in ["csv", "pdf"]:
        raise HTTPException(status_code=400, detail="Invalid format. Supported formats: 'csv', 'pdf'")

    # 1. Fleet Utilization Report
    if report_type == "fleet_utilization":
        title = "Fleet Utilization & Asset Report"
        headers = ["Vehicle ID", "Registration", "Type", "Capacity (kg)", "Fuel", "Status", "Driver"]
        vehicles = db.query(Vehicle).all()
        rows = [
            [
                v.vehicle_id,
                v.registration_number,
                v.vehicle_type,
                str(v.capacity),
                v.fuel_type,
                v.current_status,
                v.driver.name if v.driver else "Unassigned"
            ]
            for v in vehicles
        ]

    # 2. Fuel Consumption Report
    elif report_type == "fuel_consumption":
        title = "Fuel Consumption & Cost Report"
        headers = ["Vehicle ID", "Registration", "Type", "Trips", "Distance (km)", "Fuel (L)", "Cost (INR)", "Economy"]
        vehicles = db.query(Vehicle).all()
        trips = db.query(Trip).all()
        rows = []
        for v in vehicles:
            v_trips = [t for t in trips if t.vehicle_id == v.id]
            dist = sum(t.distance_km for t in v_trips if t.distance_km)
            eff = FUEL_CONSUMPTION_KM_PER_LITER.get(v.vehicle_type, 4.5)
            fuel = round(dist / eff, 1) if eff > 0 else 0.0
            cost = round(fuel * BENCHMARK_DIESEL_PRICE, 2)
            rows.append([
                v.vehicle_id,
                v.registration_number,
                v.vehicle_type,
                str(len(v_trips)),
                f"{dist:.1f}",
                f"{fuel:.1f}",
                f"Rs.{cost:.2f}",
                f"{eff} km/L"
            ])

    # 3. Driver Performance Report
    elif report_type == "driver_performance":
        title = "Driver Performance & Attendance Report"
        headers = ["Driver ID", "Name", "License", "Phone", "Attendance %", "Rating", "Assigned Asset", "Status"]
        drivers = db.query(Driver).all()
        rows = [
            [
                d.driver_id,
                d.name,
                d.license_number,
                d.phone,
                f"{d.attendance:.1f}%",
                f"{d.performance:.1f}",
                d.vehicles[0].vehicle_id if d.vehicles and len(d.vehicles) > 0 else "None",
                "Active" if d.is_active else "Inactive"
            ]
            for d in drivers
        ]

    # 4. Delivery Performance Report
    elif report_type == "delivery_performance":
        title = "Shipment Delivery Performance Report"
        headers = ["Tracking ID", "Customer", "Origin", "Destination", "Distance (km)", "Progress %", "Status"]
        shipments = db.query(Shipment).all()
        rows = [
            [
                s.tracking_number,
                s.customer_name,
                s.origin,
                s.destination,
                f"{s.distance_km:.1f}",
                f"{s.progress:.0f}%",
                s.status
            ]
            for s in shipments
        ]

    # 5. Maintenance Report
    elif report_type == "maintenance":
        title = "Vehicle Maintenance & Expenditure Report"
        headers = ["Service ID", "Vehicle", "Category", "Priority", "Scheduled", "Cost (INR)", "Status", "Center"]
        records = db.query(MaintenanceRecord).all()
        rows = [
            [
                m.maintenance_id,
                m.vehicle.vehicle_id if m.vehicle else f"#{m.vehicle_id}",
                m.category,
                m.priority,
                m.scheduled_date.strftime("%Y-%m-%d") if m.scheduled_date else "-",
                f"Rs.{m.cost:.2f}",
                m.status,
                m.service_center or "Central Depot"
            ]
            for m in records
        ]

    else:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid report_type '{report_type}'. Allowed: 'fleet_utilization', 'fuel_consumption', 'driver_performance', 'delivery_performance', 'maintenance'"
        )

    filename_base = f"fleetflow_{report_type}_{datetime.utcnow().strftime('%Y%m%d')}"

    if format == "csv":
        csv_data = build_csv_data(headers, rows)
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="{filename_base}.csv"',
                "Content-Type": "text/csv; charset=utf-8"
            }
        )

    # PDF format
    pdf_bytes = build_pure_python_pdf(title, headers, rows)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename_base}.pdf"',
            "Content-Type": "application/pdf"
        }
    )
