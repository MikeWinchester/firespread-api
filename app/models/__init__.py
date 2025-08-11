# app/models/__init__.py
"""
Pydantic models for the FireSpread API
"""

from .simulation import (
    VegetationType,
    FireCellState,
    SimulationStatus,
    IgnitionPoint,
    SimulationParameters,
    FireCell,
    SimulationRequest,
    SimulationResponse,
    SimulationMetadata,
    ErrorResponse
)

from .scenario import (
    ScenarioData,
    ScenarioCreateRequest,
    ScenarioUpdateRequest,
    ScenarioListResponse,
    ScenarioStats
)

__all__ = [
    # Simulation models
    "VegetationType",
    "FireCellState", 
    "SimulationStatus",
    "IgnitionPoint",
    "SimulationParameters",
    "FireCell",
    "SimulationRequest",
    "SimulationResponse", 
    "SimulationMetadata",
    "ErrorResponse",
    # Scenario models
    "ScenarioData",
    "ScenarioCreateRequest",
    "ScenarioUpdateRequest", 
    "ScenarioListResponse",
    "ScenarioStats"
]