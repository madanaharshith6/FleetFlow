from typing import Dict, List, Any
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        # Map shipment_id -> list of active WebSockets
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # Global listeners (for live fleet monitoring dashboard)
        self.global_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket, shipment_id: str):
        await websocket.accept()
        if shipment_id not in self.active_connections:
            self.active_connections[shipment_id] = []
        self.active_connections[shipment_id].append(websocket)

    def disconnect(self, websocket: WebSocket, shipment_id: str):
        if shipment_id in self.active_connections:
            if websocket in self.active_connections[shipment_id]:
                self.active_connections[shipment_id].remove(websocket)
            if not self.active_connections[shipment_id]:
                del self.active_connections[shipment_id]

    async def connect_global(self, websocket: WebSocket):
        await websocket.accept()
        self.global_connections.append(websocket)

    def disconnect_global(self, websocket: WebSocket):
        if websocket in self.global_connections:
            self.global_connections.remove(websocket)

    async def broadcast_to_shipment(self, shipment_id: str, message: Dict[str, Any]):
        """Send message to all clients tracking a specific shipment."""
        # Also notify global fleet dashboard clients
        for conn in list(self.global_connections):
            try:
                await conn.send_json(message)
            except Exception:
                self.disconnect_global(conn)

        if shipment_id in self.active_connections:
            for connection in list(self.active_connections[shipment_id]):
                try:
                    await connection.send_json(message)
                except Exception:
                    self.disconnect(connection, shipment_id)


manager = ConnectionManager()
