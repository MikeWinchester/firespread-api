import json
from fastapi import APIRouter, WebSocket
from app.models.schemas import SimulationResponse

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, simulation_id: str):
        await websocket.accept()
        self.active_connections[simulation_id] = websocket

    def disconnect(self, simulation_id: str):
        if simulation_id in self.active_connections:
            del self.active_connections[simulation_id]

    async def send_update(self, simulation_id: str, data: SimulationResponse):
        if simulation_id in self.active_connections:
            websocket = self.active_connections[simulation_id]
            try:
                await websocket.send_json(data.dict())
            except Exception as e:
                print(f"Error sending WebSocket update: {e}")
                self.disconnect(simulation_id)

manager = ConnectionManager()

async def websocket_simulation(websocket: WebSocket, simulation_id: str):
    await manager.connect(websocket, simulation_id)
    try:
        while True:
            await websocket.receive_text()
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        manager.disconnect(simulation_id)

router = APIRouter()
router.add_api_websocket_route("/simulations/{simulation_id}", websocket_simulation)