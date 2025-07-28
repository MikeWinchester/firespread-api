# Endpoints de la API
from .simulations import router as simulations_router
from .scenarios import router as scenarios_router

__all__ = ["simulations_router", "scenarios_router"]