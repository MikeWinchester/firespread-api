# app/utils/__init__.py
"""
Utility functions and helpers
"""

from .logging import setup_logging, get_logger, FireSpreadLogger

__all__ = [
    "setup_logging",
    "get_logger",
    "FireSpreadLogger"
]