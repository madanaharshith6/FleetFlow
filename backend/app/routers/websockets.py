import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..services.websocket_manager import manager

logger = logging.getLogger("fleetflow.websocket")
router = APIRouter(tags=["WebSockets"])


@router.websocket("/ws/shipments/{shipment_id}")
async def websocket_shipment_tracking(websocket: WebSocket, shipment_id: str):
    await manager.connect(websocket, shipment_id)
    try:
        # Send initial confirmation
        await websocket.send_json({
            "type": "connection_established",
            "shipment_id": shipment_id,
            "message": f"Connected to real-time telemetry stream for shipment {shipment_id}"
        })
        while True:
            # Keep connection alive & handle incoming pings
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket, shipment_id)
    except Exception as e:
        logger.error(f"WebSocket error for shipment {shipment_id}: {e}")
        manager.disconnect(websocket, shipment_id)


@router.websocket("/ws/fleet")
async def websocket_fleet_overview(websocket: WebSocket):
    await manager.connect_global(websocket)
    try:
        await websocket.send_json({
            "type": "fleet_stream_connected",
            "message": "Connected to global fleet telemetry feed"
        })
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect_global(websocket)
    except Exception as e:
        logger.error(f"Global WebSocket error: {e}")
        manager.disconnect_global(websocket)
