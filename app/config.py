"""
Configuration settings for the FireSpread Simulator API
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Project information
    PROJECT_NAME: str = "FireSpread Simulator API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Backend API for fire spread simulation using Rothermel model"
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # Server configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8000))
    RELOAD: bool = os.getenv("RELOAD", "false").lower() == "true"
    
    # API Documentation
    ENABLE_DOCS: bool = os.getenv("ENABLE_DOCS", "true").lower() == "true"
    
    # CORS settings
    ALLOWED_HOSTS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "https://your-frontend-domain.com"
    ]
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "")
    
    # Simulation settings
    MAX_SIMULATIONS: int = int(os.getenv("MAX_SIMULATIONS", 100))
    MAX_SIMULATION_TIME: int = int(os.getenv("MAX_SIMULATION_TIME", 300))  # seconds
    SIMULATION_STEP_INTERVAL: float = float(os.getenv("SIMULATION_STEP_INTERVAL", 1.0))  # seconds
    MAX_FIRE_CELLS_PER_SIMULATION: int = int(os.getenv("MAX_FIRE_CELLS_PER_SIMULATION", 1000))
    
    # WebSocket settings
    WEBSOCKET_HEARTBEAT_INTERVAL: int = int(os.getenv("WEBSOCKET_HEARTBEAT_INTERVAL", 30))
    
    # Logging settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "json")  # json or text
    
    # Fire model settings
    GRID_RESOLUTION: float = float(os.getenv("GRID_RESOLUTION", 0.01))  # Grid cell size
    BASE_SPREAD_RATE_MULTIPLIER: float = float(os.getenv("BASE_SPREAD_RATE_MULTIPLIER", 0.00001))
    
    # Performance settings
    MAX_CONCURRENT_SIMULATIONS: int = int(os.getenv("MAX_CONCURRENT_SIMULATIONS", 10))
    
    # Database settings (for future use)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./firespread.db")
    
    # Redis settings (for future use)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Ignora variables no definidas en el .env


# Create settings instance
settings = Settings()

# Environment-specific overrides
if settings.ENVIRONMENT == "production":
    settings.DEBUG = False
    settings.LOG_LEVEL = "WARNING"
    settings.RELOAD = False
elif settings.ENVIRONMENT == "testing":
    settings.DATABASE_URL = "sqlite:///./test_firespread.db"
    settings.MAX_SIMULATION_TIME = 60  # Shorter for tests