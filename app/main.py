"""
FireSpread Simulator API - Main Application
FastAPI application for fire spread simulation using Rothermel model
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.utils.logging import setup_logging
from app.api.routes import health, simulations, scenarios, websockets
from app.core.simulation_manager import SimulationManager

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Global simulation manager instance
simulation_manager = SimulationManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting FireSpread Simulator Backend...")
    logger.info("Rothermel fire model implementation ready")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down FireSpread Simulator Backend...")
    await simulation_manager.shutdown()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for fire spread simulation using Rothermel model",
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(health.router, tags=["health"])
app.include_router(simulations.router, prefix="/api", tags=["simulations"])
app.include_router(scenarios.router, prefix="/api", tags=["scenarios"])
app.include_router(websockets.router, tags=["websockets"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "FireSpread Simulator API",
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/api/health"
    }