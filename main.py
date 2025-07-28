from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from app.core.config import settings
from app.api.endpoints import simulations, scenarios
from app.api.websocket import router as ws_router
from app.core.logging import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting FireSpread API")
    logger.info(f"Allowed origins: {settings.allow_origins}")
    
    # Aquí podrías inicializar conexiones a DB, etc.
    # Ejemplo: 
    # await database.connect()
    # await cache.initialize()
    
    yield
    
    # Shutdown
    logger.info("Shutting down FireSpread API")
    # Ejemplo:
    # await database.disconnect()

app = FastAPI(
    title="FireSpread API",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# Middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allow_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(simulations.router, prefix="/api/simulations")
app.include_router(scenarios.router, prefix="/api/scenarios")
app.include_router(ws_router, prefix="/ws")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": app.version}