"""
Health check endpoints
"""

from fastapi import APIRouter, Depends
from datetime import datetime
from typing import Dict

from app.config import settings
from app.api.deps import get_simulation_manager
from app.core.simulation_manager import SimulationManager

router = APIRouter()


@router.get("/api/health")
async def health_check(
    simulation_manager: SimulationManager = Depends(get_simulation_manager)
) -> Dict:
    """
    Health check endpoint
    
    Returns:
        Health status and system information
    """
    manager_stats = simulation_manager.get_manager_stats()
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "simulations_active": manager_stats["simulations"]["running"],
        "simulations_total": manager_stats["simulations"]["total"],
        "fire_cells_total": manager_stats["fire_statistics"]["total_fire_cells"],
        "websocket_connections": manager_stats["websocket_connections"],
        "scenarios_total": manager_stats["scenarios"]["total"]
    }


@router.get("/api/health/detailed")
async def detailed_health_check(
    simulation_manager: SimulationManager = Depends(get_simulation_manager)
) -> Dict:
    """
    Detailed health check with comprehensive system information
    
    Returns:
        Detailed health status and statistics
    """
    stats = simulation_manager.get_manager_stats()
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "config": {
            "max_simulations": settings.MAX_SIMULATIONS,
            "max_concurrent_simulations": settings.MAX_CONCURRENT_SIMULATIONS,
            "max_simulation_time": settings.MAX_SIMULATION_TIME,
            "simulation_step_interval": settings.SIMULATION_STEP_INTERVAL,
            "grid_resolution": settings.GRID_RESOLUTION
        },
        "statistics": stats
    }


@router.get("/api/health/ready")
async def readiness_check() -> Dict:
    """
    Kubernetes readiness probe endpoint
    
    Returns:
        Simple ready status
    """
    return {
        "status": "ready",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/api/health/live")
async def liveness_check() -> Dict:
    """
    Kubernetes liveness probe endpoint
    
    Returns:
        Simple alive status
    """
    return {
        "status": "alive",
        "timestamp": datetime.now().isoformat()
    }