"""
Simulation API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict

from app.models.simulation import SimulationRequest, SimulationResponse
from app.core.simulation_manager import SimulationManager
from app.api.deps import get_simulation_manager

router = APIRouter()


@router.post("/simulations", response_model=SimulationResponse)
async def create_simulation(
    request: SimulationRequest,
    simulation_manager: SimulationManager = Depends(get_simulation_manager)
) -> SimulationResponse:
    """
    Create a new fire simulation
    
    Args:
        request: Simulation creation request
        
    Returns:
        Created simulation state
    """
    simulation_id = simulation_manager.create_simulation(request)
    return simulation_manager.get_simulation_state(simulation_id)


@router.post("/simulations/{simulation_id}/start", response_model=SimulationResponse)
async def start_simulation(
    simulation_id: str,
    background_tasks: BackgroundTasks,
    simulation_manager: SimulationManager = Depends(get_simulation_manager)
) -> SimulationResponse:
    """
    Start a simulation
    
    Args:
        simulation_id: Simulation identifier
        background_tasks: FastAPI background tasks
        
    Returns:
        Started simulation state
    """
    return await simulation_manager.start_simulation(simulation_id)


@router.post("/simulations/{simulation_id}/pause", response_model=SimulationResponse)
async def pause_simulation(
    simulation_id: str,
    simulation_manager: SimulationManager = Depends(get_simulation_manager)
) -> SimulationResponse:
    """
    Pause a simulation
    
    Args:
        simulation_id: Simulation identifier
        
    Returns:
        Paused simulation state
    """
    return simulation_manager.pause_simulation(simulation_id)


@router.post("/simulations/{simulation_id}/stop", response_model=SimulationResponse)
async def stop_simulation(
    simulation_id: str,
    simulation_manager: SimulationManager = Depends(get_simulation_manager)
) -> SimulationResponse:
    """
    Stop a simulation
    
    Args:
        simulation_id: Simulation identifier
        
    Returns:
        Stopped simulation state
    """
    return simulation_manager.stop_simulation(simulation_id)


@router.get("/simulations/{simulation_id}", response_model=SimulationResponse)
async def get_simulation_status(
    simulation_id: str,
    simulation_manager: SimulationManager = Depends(get_simulation_manager)
) -> SimulationResponse:
    """
    Get simulation status and current state
    
    Args:
        simulation_id: Simulation identifier
        
    Returns:
        Current simulation state
    """
    return simulation_manager.get_simulation_state(simulation_id)


@router.get("/simulations")
async def list_simulations(
    simulation_manager: SimulationManager = Depends(get_simulation_manager)
) -> Dict:
    """
    List all simulations
    
    Returns:
        Dictionary with simulation list and statistics
    """
    return simulation_manager.list_simulations()


@router.delete("/simulations/{simulation_id}")
async def delete_simulation(
    simulation_id: str,
    simulation_manager: SimulationManager = Depends(get_simulation_manager)
) -> Dict:
    """
    Delete a simulation
    
    Args:
        simulation_id: Simulation identifier
        
    Returns:
        Success message
    """
    simulation_manager.delete_simulation(simulation_id)
    return {"message": f"Simulation {simulation_id} deleted successfully"}


@router.get("/simulations/{simulation_id}/statistics")
async def get_simulation_statistics(
    simulation_id: str,
    simulation_manager: SimulationManager = Depends(get_simulation_manager)
) -> Dict:
    """
    Get detailed simulation statistics
    
    Args:
        simulation_id: Simulation identifier
        
    Returns:
        Detailed simulation statistics
    """
    if simulation_id not in simulation_manager.simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    simulation = simulation_manager.simulations[simulation_id]
    return simulation.get_summary_statistics()