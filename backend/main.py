"""
FastAPI main application entry point for XAI Visual Quality Control.

This module initializes the FastAPI app and includes all routers.

Author: RadiKal Team
Date: 2025-01-20
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from api.routes import router, initialize_models
from db import init_db

# Create FastAPI app
app = FastAPI(
    title="XAI Visual Quality Control API",
    description="Production-grade Explainable AI module for radiographic defect detection",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Configure CORS for Makerkit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Makerkit default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router)

# Startup event: Initialize models and database
@app.on_event("startup")
async def startup_event():
    """Initialize ML models and database on application startup."""
    init_db()
    initialize_models()

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "XAI Visual Quality Control API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "health": "/api/xai-qc/health",
    }

if __name__ == "__main__":
    import sys
    import signal
    
    # Ignore SIGBREAK on Windows
    if sys.platform == "win32":
        signal.signal(signal.SIGBREAK, signal.SIG_IGN)
    
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=False,  # Disable reload on Windows
        log_level="info"
    )
