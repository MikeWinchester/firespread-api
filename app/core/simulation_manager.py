"""
Simulation Manager
Manages multiple fire simulations and WebSocket connections
"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import WebSocket, HTTPException
import logging

from app.models.simulation import SimulationRequest, SimulationResponse, SimulationStatus
from app.models.scenario import ScenarioData, ScenarioCreateRequest, ScenarioUpdateRequest
from app.core.simulation_engine import FireSimulationEngine
from app.config import settings

logger = logging.getLogger(__name__)


class SimulationManager:
    """
    Manages multiple fire simulations and their lifecycle
    
    Features:
    - Create and manage multiple concurrent simulations
    - WebSocket real-time updates
    - Scenario management (save/load configurations)
    - Resource management and cleanup
    """
    
    def __init__(self):
        # Active simulations
        self.simulations: Dict[str, FireSimulationEngine] = {}
        
        # WebSocket connections per simulation
        self.websocket_connections: Dict[str, List[WebSocket]] = {}
        
        # Stored scenarios
        self.scenarios: Dict[str, ScenarioData] = {}
        
        # Background tasks for running simulations
        self.simulation_tasks: Dict[str, asyncio.Task] = {}
        
        # Manager state
        self.is_shutdown = False
        
        logger.info("SimulationManager initialized")
    
    async def shutdown(self):
        """Gracefully shutdown the simulation manager"""
        logger.info("Shutting down SimulationManager...")
        self.is_shutdown = True
        
        # Cancel all running simulation tasks
        for simulation_id, task in self.simulation_tasks.items():
            logger.info(f"Cancelling simulation {simulation_id}")
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        # Close all WebSocket connections
        for simulation_id, connections in self.websocket_connections.items():
            for websocket in connections[:]:
                try:
                    await websocket.close()
                except Exception as e:
                    logger.warning(f"Error closing WebSocket: {e}")
        
        # Clear all data
        self.simulations.clear()
        self.websocket_connections.clear()
        self.simulation_tasks.clear()
        
        logger.info("SimulationManager shutdown complete")
    
    def create_simulation(self, request: SimulationRequest) -> str:
        """
        Create a new fire simulation
        
        Args:
            request: Simulation creation request
            
        Returns:
            Simulation ID
            
        Raises:
            HTTPException: If maximum simulations exceeded or validation fails
        """
        # Check simulation limits
        if len(self.simulations) >= settings.MAX_SIMULATIONS:
            raise HTTPException(
                status_code=429,
                detail=f"Maximum number of simulations ({settings.MAX_SIMULATIONS}) reached"
            )
        
        # Check concurrent running simulations
        running_count = sum(1 for sim in self.simulations.values() 
                          if sim.status == SimulationStatus.RUNNING)
        if running_count >= settings.MAX_CONCURRENT_SIMULATIONS:
            raise HTTPException(
                status_code=429,
                detail=f"Maximum concurrent simulations ({settings.MAX_CONCURRENT_SIMULATIONS}) reached"
            )
        
        # Validate ignition points
        if not request.ignitionPoints:
            raise HTTPException(
                status_code=400,
                detail="At least one ignition point is required"
            )
        
        # Generate simulation ID
        simulation_id = request.simulationId or str(uuid.uuid4())
        
        if simulation_id in self.simulations:
            raise HTTPException(
                status_code=409,
                detail=f"Simulation with ID {simulation_id} already exists"
            )
        
        # Create simulation engine
        try:
            simulation = FireSimulationEngine(
                simulation_id=simulation_id,
                parameters=request.parameters,
                ignition_points=request.ignitionPoints
            )
            
            self.simulations[simulation_id] = simulation
            self.websocket_connections[simulation_id] = []
            
            logger.info(f"Created simulation {simulation_id} with {len(request.ignitionPoints)} ignition points")
            return simulation_id
            
        except Exception as e:
            logger.error(f"Error creating simulation: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to create simulation: {str(e)}")
    
    async def start_simulation(self, simulation_id: str) -> SimulationResponse:
        """
        Start a simulation
        
        Args:
            simulation_id: Simulation identifier
            
        Returns:
            Current simulation state
            
        Raises:
            HTTPException: If simulation not found or cannot be started
        """
        if simulation_id not in self.simulations:
            raise HTTPException(status_code=404, detail="Simulation not found")
        
        simulation = self.simulations[simulation_id]
        
        if simulation.status != SimulationStatus.CREATED and simulation.status != SimulationStatus.PAUSED:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot start simulation in {simulation.status} state"
            )
        
        # Start the simulation
        simulation.start()
        
        # Create and start background task
        if simulation_id not in self.simulation_tasks:
            task = asyncio.create_task(self._run_simulation_loop(simulation_id))
            self.simulation_tasks[simulation_id] = task
        
        logger.info(f"Started simulation {simulation_id}")
        return simulation._get_current_state()
    
    async def _run_simulation_loop(self, simulation_id: str):
        """
        Background task that runs the simulation loop
        
        Args:
            simulation_id: Simulation identifier
        """
        try:
            simulation = self.simulations[simulation_id]
            logger.info(f"Starting simulation loop for {simulation_id}")
            
            while (simulation.status == SimulationStatus.RUNNING and 
                   not self.is_shutdown):
                
                # Execute simulation step
                start_time = asyncio.get_event_loop().time()
                state = simulation.step()
                step_duration = asyncio.get_event_loop().time() - start_time
                
                # Broadcast state to connected clients
                await self._broadcast_to_clients(simulation_id, state)
                
                # Log performance metrics periodically
                if simulation.current_time % 30 == 0:  # Every 30 seconds
                    logger.debug(
                        f"Simulation {simulation_id}: time={simulation.current_time}, "
                        f"cells={len(simulation.fire_grid)}, step_time={step_duration:.3f}s"
                    )
                
                # Sleep for next step (maintain real-time pace)
                sleep_time = max(0, settings.SIMULATION_STEP_INTERVAL - step_duration)
                await asyncio.sleep(sleep_time)
            
            # Simulation completed or paused
            final_state = simulation._get_current_state()
            await self._broadcast_to_clients(simulation_id, final_state)
            
            logger.info(f"Simulation loop completed for {simulation_id}, status: {simulation.status}")
            
        except asyncio.CancelledError:
            logger.info(f"Simulation loop cancelled for {simulation_id}")
            simulation.stop()
        except Exception as e:
            logger.error(f"Error in simulation loop {simulation_id}: {e}")
            simulation.status = SimulationStatus.ERROR
            try:
                error_state = simulation._get_current_state()
                await self._broadcast_to_clients(simulation_id, error_state)
            except Exception:
                pass
        finally:
            # Clean up task reference
            if simulation_id in self.simulation_tasks:
                del self.simulation_tasks[simulation_id]
    
    async def _broadcast_to_clients(self, simulation_id: str, state: SimulationResponse):
        """
        Broadcast simulation state to connected WebSocket clients
        
        Args:
            simulation_id: Simulation identifier
            state: Current simulation state
        """
        if simulation_id not in self.websocket_connections:
            return
        
        message = state.model_dump_json()
        connections = self.websocket_connections[simulation_id][:]  # Copy to avoid modification during iteration
        
        for websocket in connections:
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.warning(f"Failed to send message to WebSocket client: {e}")
                # Remove failed connection
                try:
                    self.websocket_connections[simulation_id].remove(websocket)
                except ValueError:
                    pass  # Already removed
    
    def pause_simulation(self, simulation_id: str) -> SimulationResponse:
        """
        Pause a simulation
        
        Args:
            simulation_id: Simulation identifier
            
        Returns:
            Current simulation state
        """
        if simulation_id not in self.simulations:
            raise HTTPException(status_code=404, detail="Simulation not found")
        
        simulation = self.simulations[simulation_id]
        
        if simulation.status != SimulationStatus.RUNNING:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot pause simulation in {simulation.status} state"
            )
        
        simulation.pause()
        logger.info(f"Paused simulation {simulation_id}")
        return simulation._get_current_state()
    
    def stop_simulation(self, simulation_id: str) -> SimulationResponse:
        """
        Stop a simulation
        
        Args:
            simulation_id: Simulation identifier
            
        Returns:
            Final simulation state
        """
        if simulation_id not in self.simulations:
            raise HTTPException(status_code=404, detail="Simulation not found")
        
        simulation = self.simulations[simulation_id]
        simulation.stop()
        
        # Cancel background task
        if simulation_id in self.simulation_tasks:
            task = self.simulation_tasks[simulation_id]
            task.cancel()
        
        logger.info(f"Stopped simulation {simulation_id}")
        return simulation._get_current_state()
    
    def get_simulation_state(self, simulation_id: str) -> SimulationResponse:
        """
        Get current simulation state
        
        Args:
            simulation_id: Simulation identifier
            
        Returns:
            Current simulation state
        """
        if simulation_id not in self.simulations:
            raise HTTPException(status_code=404, detail="Simulation not found")
        
        return self.simulations[simulation_id]._get_current_state()
    
    def list_simulations(self) -> Dict:
        """
        List all simulations
        
        Returns:
            Dictionary with simulation information
        """
        simulations = []
        
        for sim_id, simulation in self.simulations.items():
            state = simulation._get_current_state()
            simulations.append(state)
        
        running_count = sum(1 for sim in self.simulations.values() 
                          if sim.status == SimulationStatus.RUNNING)
        
        return {
            "simulations": simulations,
            "total": len(self.simulations),
            "running": running_count,
            "max_simulations": settings.MAX_SIMULATIONS,
            "max_concurrent": settings.MAX_CONCURRENT_SIMULATIONS
        }
    
    def delete_simulation(self, simulation_id: str):
        """
        Delete a simulation
        
        Args:
            simulation_id: Simulation identifier
        """
        if simulation_id not in self.simulations:
            raise HTTPException(status_code=404, detail="Simulation not found")
        
        # Stop simulation if running
        simulation = self.simulations[simulation_id]
        if simulation.status == SimulationStatus.RUNNING:
            self.stop_simulation(simulation_id)
        
        # Clean up
        del self.simulations[simulation_id]
        
        if simulation_id in self.websocket_connections:
            del self.websocket_connections[simulation_id]
        
        logger.info(f"Deleted simulation {simulation_id}")
    
    def add_websocket_connection(self, simulation_id: str, websocket: WebSocket):
        """
        Add WebSocket connection for simulation updates
        
        Args:
            simulation_id: Simulation identifier
            websocket: WebSocket connection
        """
        if simulation_id not in self.websocket_connections:
            self.websocket_connections[simulation_id] = []
        
        self.websocket_connections[simulation_id].append(websocket)
        logger.info(f"Added WebSocket connection for simulation {simulation_id}")
    
    def remove_websocket_connection(self, simulation_id: str, websocket: WebSocket):
        """
        Remove WebSocket connection
        
        Args:
            simulation_id: Simulation identifier
            websocket: WebSocket connection
        """
        if simulation_id in self.websocket_connections:
            try:
                self.websocket_connections[simulation_id].remove(websocket)
                logger.info(f"Removed WebSocket connection for simulation {simulation_id}")
            except ValueError:
                pass  # Already removed
    
    # ================================
    # SCENARIO MANAGEMENT
    # ================================
    
    def create_scenario(self, request: ScenarioCreateRequest) -> str:
        """
        Create a new scenario
        
        Args:
            request: Scenario creation request
            
        Returns:
            Scenario ID
        """
        scenario_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        scenario = ScenarioData(
            id=scenario_id,
            name=request.name,
            description=request.description,
            parameters=request.parameters,
            ignitionPoints=request.ignitionPoints,
            tags=request.tags or [],
            createdAt=now,
            updatedAt=now
        )
        
        self.scenarios[scenario_id] = scenario
        logger.info(f"Created scenario {scenario_id}: {request.name}")
        return scenario_id
    
    def get_scenarios(self) -> List[ScenarioData]:
        """Get all scenarios"""
        return list(self.scenarios.values())
    
    def get_scenario(self, scenario_id: str) -> ScenarioData:
        """
        Get specific scenario
        
        Args:
            scenario_id: Scenario identifier
            
        Returns:
            Scenario data
        """
        if scenario_id not in self.scenarios:
            raise HTTPException(status_code=404, detail="Scenario not found")
        
        return self.scenarios[scenario_id]
    
    def update_scenario(self, scenario_id: str, request: ScenarioUpdateRequest) -> ScenarioData:
        """
        Update scenario
        
        Args:
            scenario_id: Scenario identifier
            request: Update request
            
        Returns:
            Updated scenario data
        """
        if scenario_id not in self.scenarios:
            raise HTTPException(status_code=404, detail="Scenario not found")
        
        scenario = self.scenarios[scenario_id]
        
        # Update fields if provided
        if request.name is not None:
            scenario.name = request.name
        if request.description is not None:
            scenario.description = request.description
        if request.parameters is not None:
            scenario.parameters = request.parameters
        if request.ignitionPoints is not None:
            scenario.ignitionPoints = request.ignitionPoints
        if request.tags is not None:
            scenario.tags = request.tags
        
        scenario.updatedAt = datetime.now().isoformat()
        
        logger.info(f"Updated scenario {scenario_id}")
        return scenario
    
    def delete_scenario(self, scenario_id: str):
        """
        Delete scenario
        
        Args:
            scenario_id: Scenario identifier
        """
        if scenario_id not in self.scenarios:
            raise HTTPException(status_code=404, detail="Scenario not found")
        
        scenario_name = self.scenarios[scenario_id].name
        del self.scenarios[scenario_id]
        logger.info(f"Deleted scenario {scenario_id}: {scenario_name}")
    
    def get_scenario_stats(self) -> Dict:
        """Get scenario statistics"""
        total = len(self.scenarios)
        
        # Count by vegetation type
        by_vegetation = {}
        for scenario in self.scenarios.values():
            veg_type = scenario.parameters.vegetationType.value
            by_vegetation[veg_type] = by_vegetation.get(veg_type, 0) + 1
        
        # Get recent scenarios (last 5)
        recent = sorted(self.scenarios.values(), 
                       key=lambda s: s.createdAt or "", 
                       reverse=True)[:5]
        recent_ids = [s.id for s in recent if s.id]
        
        return {
            "total_scenarios": total,
            "by_vegetation_type": by_vegetation,
            "recent_scenarios": recent_ids
        }
    
    def get_manager_stats(self) -> Dict:
        """Get comprehensive manager statistics"""
        running_simulations = [s for s in self.simulations.values() 
                             if s.status == SimulationStatus.RUNNING]
        
        total_fire_cells = sum(len(s.fire_grid) for s in self.simulations.values())
        total_active_fires = sum(len(s.active_fire_cells) for s in self.simulations.values())
        
        return {
            "simulations": {
                "total": len(self.simulations),
                "running": len(running_simulations),
                "paused": sum(1 for s in self.simulations.values() if s.status == SimulationStatus.PAUSED),
                "completed": sum(1 for s in self.simulations.values() if s.status == SimulationStatus.COMPLETED),
                "error": sum(1 for s in self.simulations.values() if s.status == SimulationStatus.ERROR)
            },
            "fire_statistics": {
                "total_fire_cells": total_fire_cells,
                "total_active_fires": total_active_fires
            },
            "scenarios": {
                "total": len(self.scenarios)
            },
            "websocket_connections": sum(len(connections) for connections in self.websocket_connections.values()),
            "background_tasks": len(self.simulation_tasks)
        }