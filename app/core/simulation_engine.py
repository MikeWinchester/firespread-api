"""
Fire Simulation Engine
Core engine for running fire spread simulations using the Rothermel model
"""

import asyncio
import time
import math
import numpy as np
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass
import logging

from app.models.simulation import (
    SimulationParameters, 
    IgnitionPoint, 
    FireCell, 
    FireCellState, 
    SimulationStatus,
    SimulationResponse,
    SimulationMetadata
)
from app.core.rothermel import RothermelModel
from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class GridCell:
    """Internal grid cell for simulation calculations"""
    x: float
    y: float
    state: FireCellState = FireCellState.UNBURNED
    ignition_time: int = -1
    intensity: float = 0.0
    temperature: float = 20.0  # Ambient temperature
    fuel_moisture: float = 10.0
    burned_duration: int = 0


class FireSimulationEngine:
    """
    Fire spread simulation engine using Rothermel model
    
    This engine simulates fire spread across a grid-based landscape,
    calculating spread rates and fire behavior based on:
    - Fuel properties (vegetation type)
    - Weather conditions (wind, humidity)  
    - Topography (slope)
    - Fire physics (Rothermel model)
    """
    
    def __init__(self, simulation_id: str, parameters: SimulationParameters, 
                 ignition_points: List[IgnitionPoint]):
        """
        Initialize fire simulation engine
        
        Args:
            simulation_id: Unique simulation identifier
            parameters: Simulation parameters
            ignition_points: Initial fire ignition points
        """
        self.simulation_id = simulation_id
        self.parameters = parameters
        self.ignition_points = ignition_points
        
        # Simulation state
        self.current_time = 0
        self.status = SimulationStatus.CREATED
        self.last_update = time.time()
        
        # Grid configuration
        self.grid_resolution = settings.GRID_RESOLUTION
        self.max_simulation_time = settings.MAX_SIMULATION_TIME
        self.max_fire_cells = settings.MAX_FIRE_CELLS_PER_SIMULATION
        
        # Fire tracking
        self.fire_grid: Dict[Tuple[int, int], GridCell] = {}
        self.active_fire_cells: Set[Tuple[int, int]] = set()
        self.fire_perimeter: Set[Tuple[int, int]] = set()
        
        # Performance tracking
        self.total_cells_burned = 0
        self.peak_intensity = 0.0
        self.spread_statistics = []
        
        # Initialize fire at ignition points
        self._initialize_ignition_points()
        
        logger.info(f"Initialized simulation {simulation_id} with {len(ignition_points)} ignition points")
    
    def _coordinate_to_grid(self, x: float, y: float) -> Tuple[int, int]:
        """Convert world coordinates to grid coordinates"""
        grid_x = int(round(x / self.grid_resolution))
        grid_y = int(round(y / self.grid_resolution))
        return (grid_x, grid_y)
    
    def _grid_to_coordinate(self, grid_x: int, grid_y: int) -> Tuple[float, float]:
        """Convert grid coordinates to world coordinates"""
        x = grid_x * self.grid_resolution
        y = grid_y * self.grid_resolution
        return (x, y)
    
    def _initialize_ignition_points(self):
        """Initialize fire cells at ignition points"""
        for point in self.ignition_points:
            grid_pos = self._coordinate_to_grid(point.lng, point.lat)
            
            # Create initial fire cell
            cell = GridCell(
                x=point.lng,
                y=point.lat,
                state=FireCellState.BURNING,
                ignition_time=0,
                intensity=100.0,
                temperature=800.0,
                fuel_moisture=self.parameters.humidity * 0.5
            )
            
            self.fire_grid[grid_pos] = cell
            self.active_fire_cells.add(grid_pos)
            self.fire_perimeter.add(grid_pos)
        
        logger.debug(f"Initialized {len(self.ignition_points)} ignition points")
    
    def _get_neighboring_cells(self, grid_x: int, grid_y: int) -> List[Tuple[int, int]]:
        """Get neighboring grid cells (8-direction connectivity)"""
        neighbors = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                neighbors.append((grid_x + dx, grid_y + dy))
        return neighbors
    
    def _calculate_spread_to_neighbor(self, from_cell: GridCell, to_pos: Tuple[int, int]) -> Tuple[bool, float, float]:
        """
        Calculate if fire spreads to a neighboring cell
        
        Args:
            from_cell: Source fire cell
            to_pos: Target grid position
            
        Returns:
            Tuple of (will_ignite, intensity, temperature)
        """
        if from_cell.state != FireCellState.BURNING:
            return False, 0.0, 20.0
        
        # Calculate direction of spread
        from_pos = self._coordinate_to_grid(from_cell.x, from_cell.y)
        dx = to_pos[0] - from_pos[0]
        dy = to_pos[1] - from_pos[1]
        
        # Calculate spread direction in degrees (0=North, 90=East)
        direction = math.degrees(math.atan2(dx, dy)) % 360
        
        # Calculate distance (diagonal cells are farther)
        distance = math.sqrt(dx*dx + dy*dy) * self.grid_resolution
        
        # Get directional spread rate using Rothermel model
        spread_rate = RothermelModel.calculate_directional_spread_rate(
            self.parameters, 
            direction,
            from_cell.fuel_moisture
        )
        
        if spread_rate <= 0:
            return False, 0.0, 20.0
        
        # Convert spread rate from m/min to grid cells per second
        spread_rate_per_second = (spread_rate / 60.0) / self.grid_resolution
        
        # Calculate probability of ignition based on spread rate and distance
        ignition_probability = spread_rate_per_second / distance
        
        # Add some randomness and intensity decay
        intensity_factor = from_cell.intensity / 100.0
        random_factor = np.random.random()
        
        will_ignite = (random_factor < ignition_probability * intensity_factor * 0.8)
        
        if will_ignite:
            # Calculate new cell intensity
            base_intensity = 80.0
            
            # Environmental factors
            wind_factor = 1.0 + (self.parameters.windSpeed / 50.0)
            humidity_factor = (100 - self.parameters.humidity) / 100.0
            slope_factor = 1.0 + (self.parameters.slope / 90.0)
            
            new_intensity = base_intensity * wind_factor * humidity_factor * slope_factor
            new_intensity *= (0.7 + random_factor * 0.6)  # Add variability
            new_intensity = max(20.0, min(200.0, new_intensity))
            
            # Calculate temperature
            new_temperature = 300.0 + new_intensity * 3.0
            
            return True, new_intensity, new_temperature
        
        return False, 0.0, 20.0
    
    def _update_existing_fire_cells(self):
        """Update intensity and state of existing fire cells"""
        cells_to_remove = set()
        
        for grid_pos in list(self.active_fire_cells):
            cell = self.fire_grid[grid_pos]
            
            if cell.state == FireCellState.BURNING:
                # Reduce intensity more slowly
                decay_rate = 1.0  # Reduced from 2.0
                cell.intensity = max(0, cell.intensity - decay_rate)
                
                # Temperature follows intensity but remains visible longer
                cell.temperature = 100.0 + cell.intensity * 5.0
                
                # Transition to burned state after sufficient time or low intensity
                burn_duration = self.current_time - cell.ignition_time
                if burn_duration > 60 or cell.intensity < 5.0:  # Increased thresholds
                    cell.state = FireCellState.BURNED
                    cell.burned_duration = burn_duration
                    cells_to_remove.add(grid_pos)
                    self.total_cells_burned += 1
                    
                    # Track peak intensity
                    self.peak_intensity = max(self.peak_intensity, cell.intensity)
        
    def _spread_fire(self):
        """Calculate fire spread to new cells"""
        new_fire_cells = []
        current_perimeter = list(self.fire_perimeter)
        
        for grid_pos in current_perimeter:
            if grid_pos not in self.fire_grid:
                continue
                
            source_cell = self.fire_grid[grid_pos]
            
            # Get neighboring cells (8-direction)
            neighbors = self._get_neighboring_cells(grid_pos[0], grid_pos[1])
            
            for neighbor_pos in neighbors:
                if neighbor_pos in self.fire_grid:
                    continue
                
                # Calculate spread to neighbor with more intensity
                will_ignite, intensity, temperature = self._calculate_spread_to_neighbor(
                    source_cell, neighbor_pos
                )
                
                if will_ignite:
                    # Increase intensity for better visualization
                    intensity = min(200, intensity * 1.5)  # Boost intensity
                    temperature = min(800, temperature * 1.2)  # Higher temperature
                    
                    world_x, world_y = self._grid_to_coordinate(neighbor_pos[0], neighbor_pos[1])
                    
                    new_cell = GridCell(
                        x=world_x,
                        y=world_y,
                        state=FireCellState.BURNING,
                        ignition_time=self.current_time,
                        intensity=intensity,
                        temperature=temperature,
                        fuel_moisture=self.parameters.humidity * 0.5
                    )
                    
                    new_fire_cells.append((neighbor_pos, new_cell))
        
        # Add new fire cells to the simulation
        for grid_pos, cell in new_fire_cells:
            self.fire_grid[grid_pos] = cell
            self.active_fire_cells.add(grid_pos)
            self.fire_perimeter.add(grid_pos)
        
        self._update_fire_perimeter()
    
    def _update_fire_perimeter(self):
        """Update the fire perimeter to include only edge cells"""
        new_perimeter = set()
        
        for grid_pos in self.active_fire_cells:
            # Check if cell has unburned neighbors
            neighbors = self._get_neighboring_cells(grid_pos[0], grid_pos[1])
            has_unburned_neighbor = any(pos not in self.fire_grid for pos in neighbors)
            
            if has_unburned_neighbor:
                new_perimeter.add(grid_pos)
        
        self.fire_perimeter = new_perimeter
    
    def _calculate_spread_statistics(self):
        """Calculate spread rate and other statistics"""
        if self.current_time > 0:
            total_cells = len(self.fire_grid)
            spread_rate = total_cells / self.current_time
            self.spread_statistics.append({
                'time': self.current_time,
                'total_cells': total_cells,
                'active_cells': len(self.active_fire_cells),
                'spread_rate': spread_rate
            })
    
    def step(self) -> SimulationResponse:
        """
        Execute one simulation step
        
        Returns:
            Current simulation state
        """
        if self.status != SimulationStatus.RUNNING:
            return self._get_current_state()
        
        try:
            # Update existing fire cells
            self._update_existing_fire_cells()
            
            # Spread fire to new cells
            self._spread_fire()
            
            # Calculate statistics
            self._calculate_spread_statistics()
            
            # Increment time
            self.current_time += 1
            
            # Check termination conditions
            if len(self.active_fire_cells) == 0:
                self.status = SimulationStatus.COMPLETED
                logger.info(f"Simulation {self.simulation_id} completed - no active fires")
            elif self.current_time >= self.max_simulation_time:
                self.status = SimulationStatus.COMPLETED
                logger.info(f"Simulation {self.simulation_id} completed - max time reached")
            elif len(self.fire_grid) >= self.max_fire_cells:
                self.status = SimulationStatus.COMPLETED
                logger.info(f"Simulation {self.simulation_id} completed - max cells reached")
        
        except Exception as e:
            logger.error(f"Error in simulation step {self.simulation_id}: {e}")
            self.status = SimulationStatus.ERROR
        
        return self._get_current_state()
    
    def _get_current_state(self) -> SimulationResponse:
        """Get current simulation state as response object"""
        # Convert grid cells to FireCell objects
        fire_cells = []
        for grid_pos, cell in self.fire_grid.items():
            fire_cell = FireCell(
                x=cell.x,
                y=cell.y,
                intensity=cell.intensity,
                temperature=cell.temperature,
                burnTime=self.current_time - cell.ignition_time if cell.ignition_time >= 0 else 0,
                state=cell.state
            )
            fire_cells.append(fire_cell)
        
        # Calculate metadata
        active_fires = len(self.active_fire_cells)
        burned_cells = len([c for c in self.fire_grid.values() if c.state == FireCellState.BURNED])
        
        # Calculate average spread rate
        avg_spread_rate = 0.0
        if self.current_time > 0 and len(self.fire_grid) > 0:
            avg_spread_rate = len(self.fire_grid) / self.current_time
        
        metadata = SimulationMetadata(
            totalCells=len(self.fire_grid),
            activeFires=active_fires,
            burnedArea=burned_cells,
            estimatedDuration=self.max_simulation_time,
            spreadRate=f"{avg_spread_rate:.2f} cells/second",
            elapsedTime=self.current_time
        )
        
        return SimulationResponse(
            simulationId=self.simulation_id,
            status=self.status,
            currentTime=self.current_time,
            fireCells=fire_cells[:1000],  # Limit response size
            metadata=metadata
        )
    
    def start(self):
        """Start the simulation"""
        self.status = SimulationStatus.RUNNING
        logger.info(f"Started simulation {self.simulation_id}")
    
    def pause(self):
        """Pause the simulation"""
        self.status = SimulationStatus.PAUSED
        logger.info(f"Paused simulation {self.simulation_id}")
    
    def stop(self):
        """Stop the simulation"""
        self.status = SimulationStatus.COMPLETED
        logger.info(f"Stopped simulation {self.simulation_id}")
    
    def get_summary_statistics(self) -> Dict:
        """Get comprehensive simulation statistics"""
        return {
            'simulation_id': self.simulation_id,
            'status': self.status.value,
            'duration': self.current_time,
            'total_cells': len(self.fire_grid),
            'active_fires': len(self.active_fire_cells),
            'total_burned': self.total_cells_burned,
            'peak_intensity': self.peak_intensity,
            'fire_perimeter_length': len(self.fire_perimeter),
            'average_spread_rate': len(self.fire_grid) / max(1, self.current_time),
            'parameters': {
                'vegetation': self.parameters.vegetationType.value,
                'wind_speed': self.parameters.windSpeed,
                'wind_direction': self.parameters.windDirection,
                'humidity': self.parameters.humidity,
                'slope': self.parameters.slope
            }
        }