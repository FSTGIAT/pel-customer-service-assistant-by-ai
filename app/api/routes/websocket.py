from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.monitoring.metrics_service import metrics_service
import logging
import asyncio
import json
from datetime import datetime
from typing import Dict

router = APIRouter()
logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_timestamps: Dict[str, datetime] = {}
        self.ping_tasks: Dict[str, asyncio.Task] = {}

    async def connect(self, websocket: WebSocket, customer_id: str):
        try:
            await websocket.accept()
            if customer_id in self.active_connections:
                old_ws = self.active_connections[customer_id]
                await old_ws.close(1000, "New connection established")
                # Clean up old ping task if exists
                if customer_id in self.ping_tasks:
                    self.ping_tasks[customer_id].cancel()

            self.active_connections[customer_id] = websocket
            self.connection_timestamps[customer_id] = datetime.now()
            
            # Start ping monitoring for this connection
            self.ping_tasks[customer_id] = asyncio.create_task(
                self.monitor_connection(customer_id)
            )
            
            logger.info(f"Client {customer_id} connected. Active connections: {len(self.active_connections)}")
            
            # Send initial connection success message
            await self.send_message(customer_id, {
                "type": "connection_status",
                "status": "connected",
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Error in connect for client {customer_id}: {str(e)}")
            raise

    async def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            try:
                websocket = self.active_connections[client_id]
                # Check if connection is still open before trying to close
                if websocket.client_state.CONNECTED:
                    await websocket.close(1000, "Normal closure")
            except Exception as e:
                logger.error(f"Error closing connection for client {client_id}: {str(e)}")
            finally:
                # Clean up connection regardless of close success
                del self.active_connections[client_id]
                if client_id in self.connection_timestamps:
                    del self.connection_timestamps[client_id]
                logger.info(f"Client {client_id} disconnected. Active connections: {len(self.active_connections)}")

    async def monitor_connection(self, customer_id: str):
        """Monitor connection health with ping/pong"""
        try:
            while True:
                if customer_id in self.active_connections:
                    await self.send_message(customer_id, {
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    })
                await asyncio.sleep(30)  # Send pong every 30 seconds
        except asyncio.CancelledError:
            logger.info(f"Monitoring stopped for {customer_id}")
        except Exception as e:
            logger.error(f"Error in connection monitoring for {customer_id}: {str(e)}")
            await self.disconnect(customer_id)

    async def handle_message(self, customer_id: str, message: dict):
        """Handle different types of incoming messages"""
        try:
            message_type = message.get("type")
            
            if message_type == "ping":
                await self.send_message(customer_id, {
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })
            elif message_type == "session_start":
                self.connection_timestamps[customer_id] = datetime.now()
                await self.send_message(customer_id, {
                    "type": "session_update",
                    "status": "active",
                    "timestamp": datetime.now().isoformat()
                })
            elif message_type == "session_end":
                await self.disconnect(customer_id)

        except Exception as e:
            logger.error(f"Error handling message for {customer_id}: {str(e)}")

    async def send_message(self, customer_id: str, message: dict):
        if customer_id in self.active_connections:
            try:
                await self.active_connections[customer_id].send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to client {customer_id}: {str(e)}")
                await self.disconnect(customer_id)

manager = ConnectionManager()

@router.websocket("/ws/{customer_id}")
async def websocket_endpoint(websocket: WebSocket, customer_id: str):
    # Accept the connection first
    await websocket.accept()
    
    try:
        # Handle existing connection
        if customer_id in manager.active_connections:
            logger.info(f"Existing connection found for {customer_id}, closing...")
            old_connection = manager.active_connections[customer_id]
            del manager.active_connections[customer_id]
            try:
                await old_connection.close(1000)
            except Exception:
                pass  # Ignore errors closing old connection
            await asyncio.sleep(0.1)
        
        # Add to active connections
        manager.active_connections[customer_id] = websocket
        logger.info(f"New connection established for {customer_id}")
        
        # Main message loop
        while True:
            try:
                data = await websocket.receive_json()
                await manager.handle_message(customer_id, data)
                
                # Send metrics update
                metrics = await metrics_service.get_rate_limit_metrics(customer_id)
                queue_metrics = await metrics_service.get_queue_metrics()
                token_usage = await metrics_service.get_token_usage(customer_id)

                metrics_data = {
                    "type": "metrics_update",
                    "data": {
                        "rate_limit_metrics": metrics.__dict__,
                        "queue_metrics": queue_metrics.__dict__,
                        "token_usage": {
                            "used": token_usage.used,
                            "remaining": token_usage.remaining,
                            "reset_time": token_usage.reset_time.isoformat()
                        }
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                await manager.send_message(customer_id, metrics_data)
                await asyncio.sleep(5)  # Rate limit updates

            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for client {customer_id}")
                break
            except Exception as e:
                logger.error(f"Error in message loop for {customer_id}: {str(e)}")
                break
                
    except Exception as e:
        logger.error(f"Error in websocket_endpoint for {customer_id}: {str(e)}")
    finally:
        # Clean up connection
        if customer_id in manager.active_connections:
            del manager.active_connections[customer_id]
            logger.info(f"Connection cleaned up for {customer_id}")