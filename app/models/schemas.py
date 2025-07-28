from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from .enums import VegetationType, FireState

class IgnitionPoint(BaseModel):
    id: str
    lat: float = Field(..., ge=-1, le=1)
    lng: float = Field(..., ge=-1, le=1)
    timestamp: int

class FireCell(BaseModel):
    x: float
    y: float
    intensity: int = Field(..., ge=0, le=100)
    temperature: float
    burnTime: int
    state: FireState

class SimulationParameters(BaseModel):
    vegetationType: VegetationType
    windSpeed: int = Field(..., ge=0, le=100)
    windDirection: int = Field(..., ge=0, le=360)
    humidity: int = Field(..., ge=0, le=100)
    slope: int = Field(..., ge=0, le=45)

class SimulationResponse(BaseModel):
    simulationId: str
    status: str  # "created" | "running" | "paused" | "completed" | "error"
    currentTime: int
    fireCells: List[FireCell]
    metadata: Optional[Dict[str, float]] = None

class ScenarioBase(BaseModel):
    name: str
    description: str
    parameters: SimulationParameters
    ignitionPoints: List[IgnitionPoint]

class ScenarioCreate(ScenarioBase):
    pass

class Scenario(ScenarioBase):
    id: str
    createdAt: datetime
    updatedAt: datetime