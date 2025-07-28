from fastapi import APIRouter, HTTPException
from typing import List, Dict
from uuid import uuid4
from datetime import datetime
from app.models.schemas import Scenario, ScenarioCreate

router = APIRouter()

# Mock database
scenarios_db: Dict[str, Scenario] = {}

@router.post("/", response_model=Scenario)
async def create_scenario(scenario: ScenarioCreate):
    scenario_id = str(uuid4())
    now = datetime.now()
    new_scenario = Scenario(
        id=scenario_id,
        createdAt=now,
        updatedAt=now,
        **scenario.dict()
    )
    scenarios_db[scenario_id] = new_scenario
    return new_scenario

@router.get("/", response_model=List[Scenario])
async def list_scenarios():
    return list(scenarios_db.values())

@router.get("/{scenario_id}", response_model=Scenario)
async def get_scenario(scenario_id: str):
    if scenario_id not in scenarios_db:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenarios_db[scenario_id]

@router.put("/{scenario_id}", response_model=Scenario)
async def update_scenario(scenario_id: str, scenario: ScenarioCreate):
    if scenario_id not in scenarios_db:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    updated = Scenario(
        id=scenario_id,
        createdAt=scenarios_db[scenario_id].createdAt,
        updatedAt=datetime.now(),
        **scenario.dict()
    )
    scenarios_db[scenario_id] = updated
    return updated

@router.delete("/{scenario_id}")
async def delete_scenario(scenario_id: str):
    if scenario_id not in scenarios_db:
        raise HTTPException(status_code=404, detail="Scenario not found")
    del scenarios_db[scenario_id]
    return {"message": "Scenario deleted"}