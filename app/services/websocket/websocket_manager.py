# app/services/websocket/websocket_manager.py

from fastapi import WebSocket
from typing import Dict, Set, Optional
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.customer_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, customer_id: str):
        await websocket.accept()
        if customer_id not in self.active_connections:
            self.active_connections[customer_id] = set()
        self.active_connections[customer_id].add(websocket)
        logger.info(f"New WebSocket connection for customer {customer_id}")

    async def disconnect(self, websocket: WebSocket, customer_id: str):
        self.active_connections[customer_id].remove(websocket)
        if not self.active_connections[customer_id]:
            del self.active_connections[customer_id]
        logger.info(f"WebSocket disconnected for customer {customer_id}")

    async def broadcast_metrics(self, customer_id: str, metrics: dict):
        """Broadcast metrics to all connected clients for a customer"""
        if customer_id in self.active_connections:
            dead_connections = set()
            for connection in self.active_connections[customer_id]:
                try:
                    await connection.send_json({
                        "type": "metrics_update",
                        "data": metrics,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                except Exception as e:
                    logger.error(f"Error broadcasting to connection: {e}")
                    dead_connections.add(connection)
            
            # Clean up dead connections
            for dead in dead_connections:
                self.active_connections[customer_id].remove(dead)

    async def send_alert(self, customer_id: str, alert_type: str, message: str):
        """Send alert to specific customer connections"""
        if customer_id in self.active_connections:
            for connection in self.active_connections[customer_id]:
                try:
                    await connection.send_json({
                        "type": "alert",
                        "alert_type": alert_type,
                        "message": message,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                except Exception as e:
                    logger.error(f"Error sending alert: {e}")

websocket_manager = WebSocketManager()