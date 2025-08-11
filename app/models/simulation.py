"""
Pydantic models for fire spread simulation
"""

from pydantic import BaseModel, Field
from enum import Enum
from typing import List, Dict, Optional, Any


class VegetationType(str, Enum):
    """Types of vegetation for fire simulation"""
    FOREST = "forest"
    GRASSLAND = "grassland"
    SHRUBLAND = "shrubland"
    AGRICULTURAL = "agricultural"
    URBAN = "urban"


class FireCellState(str, Enum):
    """States of fire cells"""
    UNBURNED = "unburned"
    BURNING = "burning"
    BURNED = "burned"


class SimulationStatus(str, Enum):
    """Simulation status values"""
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


class IgnitionPoint(BaseModel):
    """Ignition point model"""
    id: str
    lat: float = Field(..., ge=-90, le=90, description="Latitude between -90 and 90")
    lng: float = Field(..., ge=-180, le=180, description="Longitude between -180 and 180")
    timestamp: int = Field(..., description="Unix timestamp when point was created")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "ignition_001",
                "lat": -34.6037,
                "lng": -58.3816,
                "timestamp": 1640995200
            }
        }


class SimulationParameters(BaseModel):
    """Parameters for fire simulation"""
    vegetationType: VegetationType = Field(..., description="Type of vegetation")
    windSpeed: float = Field(..., ge=0, le=100, description="Wind speed in m/s")
    windDirection: float = Field(..., ge=0, le=360, description="Wind direction in degrees (0=North)")
    humidity: float = Field(..., ge=0, le=100, description="Relative humidity percentage")
    slope: float = Field(..., ge=0, le=45, description="Terrain slope angle in degrees")

    class Config:
        json_schema_extra = {
            "example": {
                "vegetationType": "forest",
                "windSpeed": 15.5,
                "windDirection": 270,
                "humidity": 45,
                "slope": 10
            }
        }


class FireCell(BaseModel):
    """Individual fire cell in the simulation grid"""
    x: float = Field(..., description="X coordinate (longitude-based)")
    y: float = Field(..., description="Y coordinate (latitude-based)")
    intensity: float = Field(..., ge=0, description="Fire intensity (0-200)")
    temperature: float = Field(..., ge=0, description="Temperature in Celsius")
    burnTime: int = Field(..., ge=0, description="Time since ignition in seconds")
    state: FireCellState = Field(..., description="Current state of the cell")

    class Config:
        json_schema_extra = {
            "example": {
                "x": -58.3816,
                "y": -34.6037,
                "intensity": 85.5,
                "temperature": 450.0,
                "burnTime": 120,
                "state": "burning"
            }
        }


class SimulationRequest(BaseModel):
    """Request to create/start a simulation"""
    parameters: SimulationParameters = Field(..., description="Simulation parameters")
    ignitionPoints: List[IgnitionPoint] = Field(..., description="Initial ignition points")
    simulationId: Optional[str] = Field(None, description="Optional custom simulation ID")

    class Config:
        json_schema_extra = {
            "example": {
                "parameters": {
                    "vegetationType": "forest",
                    "windSpeed": 15.5,
                    "windDirection": 270,
                    "humidity": 45,
                    "slope": 10
                },
                "ignitionPoints": [
                    {
                        "id": "ignition_001",
                        "lat": -34.6037,
                        "lng": -58.3816,
                        "timestamp": 1640995200
                    }
                ]
            }
        }


class SimulationMetadata(BaseModel):
    """Metadata about simulation progress"""
    totalCells: int = Field(..., description="Total number of fire cells")
    activeFires: int = Field(..., description="Number of currently burning cells")
    burnedArea: int = Field(..., description="Number of burned cells")
    estimatedDuration: int = Field(..., description="Estimated total duration in seconds")
    spreadRate: str = Field(..., description="Current spread rate description")
    elapsedTime: int = Field(..., description="Elapsed simulation time in seconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "totalCells": 150,
                "activeFires": 25,
                "burnedArea": 125,
                "estimatedDuration": 300,
                "spreadRate": "2.5 cells/second",
                "elapsedTime": 60
            }
        }


class SimulationResponse(BaseModel):
    """Response with simulation state"""
    simulationId: str = Field(..., description="Unique simulation identifier")
    status: SimulationStatus = Field(..., description="Current simulation status")
    currentTime: int = Field(..., description="Current simulation time in seconds")
    fireCells: List[FireCell] = Field(..., description="Current fire cells")
    metadata: Optional[SimulationMetadata] = Field(None, description="Additional simulation metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "simulationId": "sim_abc123",
                "status": "running",
                "currentTime": 60,
                "fireCells": [
                    {
                        "x": -58.3816,
                        "y": -34.6037,
                        "intensity": 85.5,
                        "temperature": 450.0,
                        "burnTime": 60,
                        "state": "burning"
                    }
                ],
                "metadata": {
                    "totalCells": 25,
                    "activeFires": 15,
                    "burnedArea": 10,
                    "estimatedDuration": 300,
                    "spreadRate": "2.1 cells/second",
                    "elapsedTime": 60
                }
            }
        }


class SimulationListResponse(BaseModel):
    """Response for listing simulations"""
    simulations: List[SimulationResponse] = Field(..., description="List of simulations")
    total: int = Field(..., description="Total number of simulations")
    active: int = Field(..., description="Number of active simulations")


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    timestamp: str = Field(..., description="Error timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "Simulation not found",
                "detail": "No simulation exists with ID: sim_abc123",
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }