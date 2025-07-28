import numpy as np
from typing import List, Dict
from datetime import datetime
import uuid
from app.models.schemas import (
    SimulationParameters,
    IgnitionPoint,
    FireCell,
    SimulationResponse
)

class FireSimulationEngine:
    def __init__(self, parameters: SimulationParameters, ignition_points: List[IgnitionPoint]):
        self.id = str(uuid.uuid4())
        self.parameters = parameters
        self.ignition_points = ignition_points
        self.status = "created"
        self.current_time = 0
        self.fire_cells: List[FireCell] = []
        self.grid_size = 100
        self.grid = np.zeros((self.grid_size, self.grid_size))
        self.start_time = datetime.now()
        
    def start(self):
        self.status = "running"
        self.start_time = datetime.now()
        
    def pause(self):
        self.status = "paused"
        
    def stop(self):
        self.status = "completed"
        
    def update(self):
        if self.status != "running":
            return
            
        self.current_time += 1
        new_fire_cells: List[FireCell] = []
        
        for point in self.ignition_points:
            grid_x = int((point.lng + 1) * (self.grid_size / 2))
            grid_y = int((1 - point.lat) * (self.grid_size / 2))
            grid_x = max(0, min(self.grid_size - 1, grid_x))
            grid_y = max(0, min(self.grid_size - 1, grid_y))
            
            self._spread_fire(grid_x, grid_y)
            
        burning_cells = np.argwhere(self.grid == 1)
        for x, y in burning_cells:
            norm_x = (x / self.grid_size) * 2 - 1
            norm_y = 1 - (y / self.grid_size) * 2
            
            intensity = 50 + np.random.randint(0, 50)
            temperature = 200 + intensity * 8
            
            new_fire_cells.append(FireCell(
                x=float(norm_x),
                y=float(norm_y),
                intensity=intensity,
                temperature=temperature,
                burnTime=self.current_time,
                state="burning"
            ))
            
        self.fire_cells = new_fire_cells
        
    def _spread_fire(self, x: int, y: int):
        wind_effect = self.parameters.windDirection / 360
        humidity_effect = (100 - self.parameters.humidity) / 100
        spread_prob = 0.3 * humidity_effect * (1 + self.parameters.windSpeed / 100)
        
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                    
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.grid_size and 0 <= ny < self.grid_size:
                    if self.grid[nx, ny] == 0 and np.random.random() < spread_prob:
                        self.grid[nx, ny] = 1
                        
        if self.current_time > 5 + np.random.randint(0, 10):
            self.grid[x, y] = 2
            
    def get_state(self) -> SimulationResponse:
        return SimulationResponse(
            simulationId=self.id,
            status=self.status,
            currentTime=self.current_time,
            fireCells=self.fire_cells,
            metadata={
                "totalArea": len(self.fire_cells) * 0.01,
                "burnedArea": sum(1 for cell in self.fire_cells if cell.state == "burned") * 0.01,
                "simulationDuration": (datetime.now() - self.start_time).total_seconds()
            }
        )