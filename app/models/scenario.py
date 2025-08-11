"""
Pydantic models for fire simulation scenarios
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

from app.models.simulation import SimulationParameters, IgnitionPoint


class ScenarioData(BaseModel):
    """Fire simulation scenario data"""
    id: Optional[str] = Field(None, description="Unique scenario identifier")
    name: str = Field(..., min_length=1, max_length=100, description="Scenario name")
    description: str = Field(..., min_length=1, max_length=500, description="Scenario description")
    parameters: SimulationParameters = Field(..., description="Simulation parameters")
    ignitionPoints: List[IgnitionPoint] = Field(..., description="Initial ignition points")
    createdAt: Optional[str] = Field(None, description="Creation timestamp")
    updatedAt: Optional[str] = Field(None, description="Last update timestamp")
    tags: Optional[List[str]] = Field(default_factory=list, description="Scenario tags")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "scenario_001",
                "name": "Forest Fire - High Wind",
                "description": "Forest fire scenario with high wind conditions and low humidity",
                "parameters": {
                    "vegetationType": "forest",
                    "windSpeed": 25.0,
                    "windDirection": 270,
                    "humidity": 30,
                    "slope": 15
                },
                "ignitionPoints": [
                    {
                        "id": "ignition_001",
                        "lat": -34.6037,
                        "lng": -58.3816,
                        "timestamp": 1640995200
                    }
                ],
                "tags": ["forest", "high-wind", "dry-conditions"],
                "createdAt": "2024-01-01T12:00:00Z",
                "updatedAt": "2024-01-01T12:00:00Z"
            }
        }


class ScenarioCreateRequest(BaseModel):
    """Request to create a new scenario"""
    name: str = Field(..., min_length=1, max_length=100, description="Scenario name")
    description: str = Field(..., min_length=1, max_length=500, description="Scenario description")
    parameters: SimulationParameters = Field(..., description="Simulation parameters")
    ignitionPoints: List[IgnitionPoint] = Field(..., description="Initial ignition points")
    tags: Optional[List[str]] = Field(default_factory=list, description="Scenario tags")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Grassland Fire - Moderate Conditions",
                "description": "Typical grassland fire with moderate wind and normal humidity",
                "parameters": {
                    "vegetationType": "grassland",
                    "windSpeed": 12.0,
                    "windDirection": 180,
                    "humidity": 55,
                    "slope": 5
                },
                "ignitionPoints": [
                    {
                        "id": "ignition_001",
                        "lat": -35.0,
                        "lng": -59.0,
                        "timestamp": 1640995200
                    }
                ],
                "tags": ["grassland", "moderate-wind", "normal-humidity"]
            }
        }


class ScenarioUpdateRequest(BaseModel):
    """Request to update an existing scenario"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Updated scenario name")
    description: Optional[str] = Field(None, min_length=1, max_length=500, description="Updated description")
    parameters: Optional[SimulationParameters] = Field(None, description="Updated simulation parameters")
    ignitionPoints: Optional[List[IgnitionPoint]] = Field(None, description="Updated ignition points")
    tags: Optional[List[str]] = Field(None, description="Updated scenario tags")


class ScenarioListResponse(BaseModel):
    """Response for listing scenarios"""
    scenarios: List[ScenarioData] = Field(..., description="List of scenarios")
    total: int = Field(..., description="Total number of scenarios")
    
    class Config:
        json_schema_extra = {
            "example": {
                "scenarios": [
                    {
                        "id": "scenario_001",
                        "name": "Forest Fire - High Wind",
                        "description": "Forest fire scenario with high wind conditions",
                        "parameters": {
                            "vegetationType": "forest",
                            "windSpeed": 25.0,
                            "windDirection": 270,
                            "humidity": 30,
                            "slope": 15
                        },
                        "ignitionPoints": [
                            {
                                "id": "ignition_001",
                                "lat": -34.6037,
                                "lng": -58.3816,
                                "timestamp": 1640995200
                            }
                        ],
                        "tags": ["forest", "high-wind"],
                        "createdAt": "2024-01-01T12:00:00Z",
                        "updatedAt": "2024-01-01T12:00:00Z"
                    }
                ],
                "total": 1
            }
        }


class ScenarioStats(BaseModel):
    """Statistics about scenarios"""
    total_scenarios: int = Field(..., description="Total number of scenarios")
    by_vegetation_type: dict = Field(..., description="Count by vegetation type")
    recent_scenarios: List[str] = Field(..., description="Recently created scenario IDs")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_scenarios": 15,
                "by_vegetation_type": {
                    "forest": 8,
                    "grassland": 4,
                    "shrubland": 2,
                    "agricultural": 1,
                    "urban": 0
                },
                "recent_scenarios": ["scenario_015", "scenario_014", "scenario_013"]
            }
        }