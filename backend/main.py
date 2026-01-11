"""
FastAPI main application entry point for XAI Visual Quality Control.

Production-ready application with:
- Comprehensive error handling
- Rate limiting
- Health monitoring
- Security middleware
- Structured logging

Author: RadiKal Team
Date: 2025-01-20
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
import uvicorn
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from api.routes import router, initialize_models
from api import analytics_routes, review_routes, compliance_routes, custom_defects_routes, user_routes
from api import health_routes
from db import init_db
from core.middleware import (
    rate_limit_middleware,
    error_handler_middleware,
    validation_exception_handler,
    http_exception_handler,
    sqlalchemy_exception_handler,
    general_exception_handler
)

# Try to import settings (fallback to defaults if not configured)
try:
    from core.config import settings
    PRODUCTION_MODE = settings.ENVIRONMENT == "production"
except:
    PRODUCTION_MODE = False
    settings = None

# Setup logging
def setup_logging():
    """Configure production-grade logging."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    log_level = logging.INFO if PRODUCTION_MODE else logging.DEBUG
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        log_dir / "app.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(log_level)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

setup_logging()
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="RadiKal XAI Quality Control API",
    description="Production-grade Explainable AI system for radiographic defect detection with enterprise features",
    version="2.0.0",
    docs_url="/api/docs" if not PRODUCTION_MODE else None,  # Disable docs in production
    redoc_url="/api/redoc" if not PRODUCTION_MODE else None,
)

# Configure CORS with restricted methods/headers for security
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:3001",
]
if settings and settings.ALLOWED_ORIGINS:
    allowed_origins.extend(settings.ALLOWED_ORIGINS)

# Secure CORS configuration
ALLOWED_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
ALLOWED_HEADERS = [
    "Authorization",
    "Content-Type",
    "Accept",
    "Origin",
    "X-Requested-With",
    "X-CSRF-Token",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=ALLOWED_METHODS,  # Restricted from "*"
    allow_headers=ALLOWED_HEADERS,  # Restricted from "*"
    expose_headers=["X-RateLimit-Remaining", "X-RateLimit-Limit"],
)

# Add security headers middleware
try:
    from core.middleware.security_headers import security_headers_middleware
    app.middleware("http")(security_headers_middleware)
    logger.info("[OK] Security headers middleware enabled")
except ImportError:
    logger.warning("[WARN] Security headers middleware not available")

# Add production middlewares
app.middleware("http")(error_handler_middleware)
if not settings or settings.RATE_LIMIT_ENABLED:
    app.middleware("http")(rate_limit_middleware)

# Register exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include routers
app.include_router(health_routes.router)  # Health checks first
app.include_router(router)

# Phase 2/3: Include advanced enterprise routers
try:
    from api import sso_routes, executive_routes, integration_routes
    app.include_router(sso_routes.router)  # SSO/SAML authentication
    app.include_router(executive_routes.router)  # Executive dashboard
    app.include_router(integration_routes.router)  # ERP/MES integration
    logger.info("[OK] Phase 2/3 enterprise routes loaded successfully")
except ImportError as e:
    logger.warning(f"[WARN] Phase 2/3 routes not available: {e}")

# Phase 3: Include advanced analytics and compliance routers
try:
    from api import federated_routes, bi_routes
    app.include_router(federated_routes.router)  # Federated learning
    app.include_router(bi_routes.router)  # BI connectors
    logger.info("[OK] Phase 3 analytics routes loaded successfully")
except ImportError as e:
    logger.warning(f"[WARN] Phase 3 routes not available: {e}")

app.include_router(analytics_routes.router)
app.include_router(review_routes.router)
app.include_router(compliance_routes.router)
app.include_router(custom_defects_routes.router)
app.include_router(user_routes.router)

# Startup event: Initialize models and database
@app.on_event("startup")
async def startup_event():
    """Initialize ML models and database on application startup."""
    logger.info("=" * 80)
    logger.info(f"Starting RadiKal XAI Quality Control API v2.0.0")
    logger.info(f"Environment: {'Production' if PRODUCTION_MODE else 'Development'}")
    logger.info("=" * 80)
    
    try:
        logger.info("Starting rate limiter cleanup task...")
        from core.middleware.rate_limiter import rate_limiter
        await rate_limiter.start_cleanup()
        logger.info("[OK] Rate limiter started")
        
        logger.info("Loading ML models...")
        initialize_models()
        logger.info("[OK] Models loaded")
        
        logger.info("=" * 80)
        logger.info("[START] Application startup complete")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"[ERROR] Startup failed: {e}", exc_info=True)
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    logger.info("Shutting down application...")
    
    # Stop rate limiter cleanup task
    try:
        from core.middleware.rate_limiter import rate_limiter
        await rate_limiter.stop_cleanup()
        logger.info("[OK] Rate limiter stopped")
    except Exception as e:
        logger.error(f"Error stopping rate limiter: {e}")
    
    logger.info("Goodbye!")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "RadiKal XAI Quality Control API",
        "version": "2.0.0",
        "environment": "production" if PRODUCTION_MODE else "development",
        "status": "operational",
        "message": "XAI Visual Quality Control API - Production Ready",
        "docs": "/docs" if not PRODUCTION_MODE else "disabled",
        "health": "/health/detailed",
        "endpoints": {
            "analysis": "/api/xai-qc/explain",
            "health": "/health",
            "metrics": "/health/metrics",
        },
        "features": [
            "AI-powered defect detection",
            "Explainable AI (XAI) - 4 methods",
            "Real-time notifications",
            "Batch processing",
            "Custom defect types",
            "Hierarchical review workflow",
            "Analytics dashboard",
            "Compliance reports"
        ]
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
