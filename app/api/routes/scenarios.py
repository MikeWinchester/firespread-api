"""
Scenario management API endpoints
"""

from fastapi import APIRouter, Depends
from typing import List, Dict

from app.models.scenario import ScenarioData, ScenarioCreateRequest, ScenarioUpdateRequest, ScenarioListResponse
from app.core.simulation_manager import SimulationManager
from app.api.deps import get_simulation_manager

router = APIRouter()


@router.get("/scenarios", response_model=ScenarioListResponse)
async def get_scenarios(
    simulation_manager: SimulationManager = Depends(get_simulation_manager)
) -> ScenarioListResponse:
    """
    Get all scenarios
    
    Returns:
        List of all scenarios
    """
    scenarios = simulation_manager.get_scenarios()
    return ScenarioListResponse(
        scenarios=scenarios,
        total=len(scenarios)
    )


@router.get("/scenarios/{scenario_id}", response_model=ScenarioData)
async def get_scenario(
    scenario_id: str,
    simulation_manager: SimulationManager = Depends(get_simulation_manager)
) -> ScenarioData:
    """
    Get a specific scenario
    
    Args:
        scenario_id: Scenario identifier
        
    Returns:
        Scenario data
    """
    return simulation_manager.get_scenario(scenario_id)


@router.post("/scenarios", response_model=ScenarioData)
async def create_scenario(
    request: ScenarioCreateRequest,
    simulation_manager: SimulationManager = Depends(get_simulation_manager)
) -> ScenarioData:
    """
    Create a new scenario
    
    Args:
        request: Scenario creation request
        
    Returns:
        Created scenario data
    """
    scenario_id = simulation_manager.create_scenario(request)
    return simulation_manager.get_scenario(scenario_id)


@router.put("/scenarios/{scenario_id}", response_model=ScenarioData)
async def update_scenario(
    scenario_id: str,
    request: ScenarioUpdateRequest,
    simulation_manager: SimulationManager = Depends(get_simulation_manager)
) -> ScenarioData:
    """
    Update an existing scenario
    
    Args:
        scenario_id: Scenario identifier
        request: Scenario update request
        
    Returns:
        Updated scenario data
    """
    return simulation_manager.update_scenario(scenario_id, request)


@router.delete("/scenarios/{scenario_id}")
async def delete_scenario(
    scenario_id: str,
    simulation_manager: SimulationManager = Depends(get_simulation_manager)
) -> Dict:
    """
    Delete a scenario
    
    Args:
        scenario_id: Scenario identifier
        
    Returns:
        Success message
    """
    simulation_manager.delete_scenario(scenario_id)
    return {"message": f"Scenario {scenario_id} deleted successfully"}


@router.get("/scenarios/stats")
async def get_scenario_statistics(
    simulation_manager: SimulationManager = Depends(get_simulation_manager)
) -> Dict:
    """
    Get scenario statistics
    
    Returns:
        Scenario statistics including counts by vegetation type
    """
    return simulation_manager.get_scenario_stats()