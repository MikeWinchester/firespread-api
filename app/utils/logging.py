"""
Logging configuration for the FireSpread API
"""

import logging
import logging.config
import sys
from typing import Dict, Any

from app.config import settings


def setup_logging():
    """Setup application logging configuration"""
    
    # Define log format
    if settings.LOG_FORMAT == "json":
        log_format = '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s", "module": "%(module)s", "function": "%(funcName)s", "line": %(lineno)d}'
    else:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Logging configuration dictionary
    logging_config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": log_format,
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": settings.LOG_LEVEL,
                "formatter": "default",
                "stream": sys.stdout,
            },
            "error_console": {
                "class": "logging.StreamHandler",
                "level": "ERROR",
                "formatter": "detailed",
                "stream": sys.stderr,
            }
        },
        "loggers": {
            # Application loggers
            "app": {
                "level": settings.LOG_LEVEL,
                "handlers": ["console", "error_console"],
                "propagate": False,
            },
            "app.core.rothermel": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "app.core.simulation_engine": {
                "level": settings.LOG_LEVEL,
                "handlers": ["console"],
                "propagate": False,
            },
            "app.core.simulation_manager": {
                "level": settings.LOG_LEVEL,
                "handlers": ["console"],
                "propagate": False,
            },
            # FastAPI and Uvicorn loggers
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn.error": {
                "level": "INFO",
                "handlers": ["console", "error_console"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "fastapi": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            }
        },
        "root": {
            "level": settings.LOG_LEVEL,
            "handlers": ["console"],
        }
    }
    
    # Apply logging configuration
    logging.config.dictConfig(logging_config)
    
    # Set specific log levels for noisy libraries
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("websockets").setLevel(logging.INFO)
    
    # Log startup message
    logger = logging.getLogger("app.utils.logging")
    logger.info(f"Logging configured - Level: {settings.LOG_LEVEL}, Format: {settings.LOG_FORMAT}")
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(f"app.{name}")


class FireSpreadLogger:
    """
    Custom logger class with simulation-specific methods
    """
    
    def __init__(self, name: str):
        self.logger = get_logger(name)
    
    def log_simulation_event(self, simulation_id: str, event: str, details: Dict = None):
        """Log simulation-specific events"""
        message = f"[{simulation_id}] {event}"
        if details:
            message += f" - {details}"
        self.logger.info(message)
    
    def log_fire_spread(self, simulation_id: str, cells_count: int, active_fires: int):
        """Log fire spread progress"""
        self.logger.debug(f"[{simulation_id}] Fire spread: {cells_count} total cells, {active_fires} active fires")
    
    def log_performance_metric(self, simulation_id: str, metric: str, value: float, unit: str = ""):
        """Log performance metrics"""
        self.logger.info(f"[{simulation_id}] Performance - {metric}: {value:.3f} {unit}")
    
    def log_websocket_event(self, simulation_id: str, event: str, client_count: int = None):
        """Log WebSocket events"""
        message = f"[{simulation_id}] WebSocket {event}"
        if client_count is not None:
            message += f" - {client_count} clients"
        self.logger.info(message)
    
    def log_error(self, simulation_id: str, error: Exception, context: str = ""):
        """Log errors with simulation context"""
        message = f"[{simulation_id}] Error in {context}: {str(error)}" if context else f"[{simulation_id}] Error: {str(error)}"
        self.logger.error(message, exc_info=True)