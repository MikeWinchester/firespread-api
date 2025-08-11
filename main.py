#!/usr/bin/env python3
"""
FireSpread Simulator Backend - Main Entry Point
Run this file to start the server
"""

import uvicorn
import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import settings

if __name__ == "__main__":
    print("=" * 60)
    print("🔥 FireSpread Simulator Backend")
    print("=" * 60)
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Debug Mode: {settings.DEBUG}")
    print(f"Host: {settings.HOST}")
    print(f"Port: {settings.PORT}")
    print(f"Log Level: {settings.LOG_LEVEL}")
    print("=" * 60)
    
    # Run the application
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG and settings.ENVIRONMENT == "development",
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True,
        use_colors=True,
        loop="asyncio"
    )