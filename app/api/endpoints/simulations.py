from fastapi import APIRouter, HTTPException
from typing import Dict, List
from app.models.schemas import (
    SimulationParameters,
    IgnitionPoint,
    SimulationResponse
)
from app.simulation.engine import FireSimulationEngine
from app.api.websocket import manager
import asyncio

router = APIRouter()
simulations: Dict[str, FireSimulationEngine] = {}

@router.post("/", response_model=SimulationResponse)
async def create_simulation(parameters: SimulationParameters, ignition_points: List[IgnitionPoint]):
    simulation = FireSimulationEngine(parameters, ignition_points)
    simulations[simulation.id] = simulation
    return simulation.get_state()

@router.post("/{simulation_id}/start", response_model=SimulationResponse)
async def start_simulation(simulation_id: str):
    if simulation_id not in simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    simulation = simulations[simulation_id]
    simulation.start()
    
    async def run_simulation():
        while simulation.status == "running":
            simulation.update()
            state = simulation.get_state()
            await manager.send_update(simulation_id, state)
            await asyncio.sleep(1)
            
    asyncio.create_task(run_simulation())
    return simulation.get_state()

@router.post("/{simulation_id}/pause", response_model=SimulationResponse)
async def pause_simulation(simulation_id: str):
    if simulation_id not in simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")
    simulations[simulation_id].pause()
    return simulations[simulation_id].get_state()

@router.post("/{simulation_id}/stop", response_model=SimulationResponse)
async def stop_simulation(simulation_id: str):
    if simulation_id not in simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")
    simulations[simulation_id].stop()
    return simulations[simulation_id].get_state()

@router.get("/{simulation_id}", response_model=SimulationResponse)
async def get_simulation(simulation_id: str):
    if simulation_id not in simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")
    return simulations[simulation_id].get_state()