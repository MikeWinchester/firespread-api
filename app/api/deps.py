"""
FastAPI dependencies
"""

from app.core.simulation_manager import SimulationManager

# Global simulation manager instance
_simulation_manager: SimulationManager = None


def get_simulation_manager() -> SimulationManager:
    """
    Dependency to get the global simulation manager instance
    
    Returns:
        SimulationManager instance
    """
    global _simulation_manager
    if _simulation_manager is None:
        _simulation_manager = SimulationManager()
    return _simulation_manager


# Initialize the global instance
simulation_manager = get_simulation_manager()