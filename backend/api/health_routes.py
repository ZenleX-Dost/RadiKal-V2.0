"""
Comprehensive health monitoring and metrics system.

Features:
- System health checks (CPU, memory, disk, GPU)
- Database connectivity checks
- Model availability checks
- API endpoint status
- Performance metrics
- Real-time system monitoring
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from pydantic import BaseModel
import psutil
import torch
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging
import asyncio
from pathlib import Path

from db import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/health", tags=["Health & Monitoring"])


class HealthStatus(BaseModel):
    """Health check status."""
    status: str  # healthy, degraded, unhealthy
    message: str
    checked_at: datetime


class SystemMetrics(BaseModel):
    """System resource metrics."""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    gpu_available: bool
    gpu_memory_used: Optional[float] = None
    gpu_memory_total: Optional[float] = None


class DatabaseHealth(BaseModel):
    """Database health status."""
    connected: bool
    response_time_ms: float
    active_connections: Optional[int] = None


class ModelHealth(BaseModel):
    """Model availability status."""
    model_loaded: bool
    model_path: str
    model_size_mb: Optional[float] = None


class DetailedHealthResponse(BaseModel):
    """Comprehensive health check response."""
    overall_status: str
    timestamp: datetime
    uptime_seconds: float
    version: str
    
    system: SystemMetrics
    database: DatabaseHealth
    models: Dict[str, ModelHealth]
    
    warnings: List[str] = []
    errors: List[str] = []


# Track application start time
APP_START_TIME = datetime.utcnow()


def check_system_health() -> SystemMetrics:
    """Check system resource usage."""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Check GPU
    gpu_available = torch.cuda.is_available()
    gpu_memory_used = None
    gpu_memory_total = None
    
    if gpu_available:
        try:
            gpu_memory_used = torch.cuda.memory_allocated(0) / 1024**3  # GB
            gpu_memory_total = torch.cuda.get_device_properties(0).total_memory / 1024**3
        except:
            pass
    
    return SystemMetrics(
        cpu_percent=cpu_percent,
        memory_percent=memory.percent,
        disk_percent=disk.percent,
        gpu_available=gpu_available,
        gpu_memory_used=gpu_memory_used,
        gpu_memory_total=gpu_memory_total
    )


async def check_database_health(db: Session) -> DatabaseHealth:
    """Check database connectivity and performance."""
    try:
        start_time = datetime.utcnow()
        
        # Simple connectivity test
        result = db.execute(text("SELECT 1"))
        result.fetchone()
        
        end_time = datetime.utcnow()
        response_time_ms = (end_time - start_time).total_seconds() * 1000
        
        # Try to get connection pool info (if using pooled connections)
        active_connections = None
        try:
            pool_status = db.execute(text(
                "SELECT count(*) FROM pg_stat_activity WHERE state = 'active'"
            ))
            active_connections = pool_status.fetchone()[0]
        except:
            pass
        
        return DatabaseHealth(
            connected=True,
            response_time_ms=response_time_ms,
            active_connections=active_connections
        )
    
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return DatabaseHealth(
            connected=False,
            response_time_ms=0,
            active_connections=None
        )


def check_model_health() -> Dict[str, ModelHealth]:
    """Check model availability."""
    models = {}
    
    # Check YOLOv8 classification model
    yolo_path = Path("models/yolo/classification_defect_focused/weights/best.pt")
    models["yolov8_classifier"] = ModelHealth(
        model_loaded=yolo_path.exists(),
        model_path=str(yolo_path),
        model_size_mb=yolo_path.stat().st_size / 1024**2 if yolo_path.exists() else None
    )
    
    # Check legacy model
    legacy_path = Path("models/checkpoints/best_model.pth")
    if legacy_path.exists():
        models["legacy_detector"] = ModelHealth(
            model_loaded=True,
            model_path=str(legacy_path),
            model_size_mb=legacy_path.stat().st_size / 1024**2
        )
    
    return models


@router.get("/", response_model=HealthStatus)
async def quick_health_check():
    """
    Quick health check for load balancers.
    
    Returns 200 OK if service is running.
    """
    return HealthStatus(
        status="healthy",
        message="Service is running",
        checked_at=datetime.utcnow()
    )


@router.get("/detailed", response_model=DetailedHealthResponse)
async def detailed_health_check(db: Session = Depends(get_db)):
    """
    Comprehensive health check with all system metrics.
    
    Used for:
    - Monitoring dashboards
    - Alerting systems
    - Capacity planning
    """
    warnings = []
    errors = []
    
    # Check system resources
    system = check_system_health()
    
    if system.cpu_percent > 80:
        warnings.append(f"High CPU usage: {system.cpu_percent}%")
    if system.memory_percent > 85:
        warnings.append(f"High memory usage: {system.memory_percent}%")
    if system.disk_percent > 90:
        errors.append(f"Low disk space: {100 - system.disk_percent}% free")
    
    # Check database
    database = await check_database_health(db)
    
    if not database.connected:
        errors.append("Database connection failed")
    elif database.response_time_ms > 1000:
        warnings.append(f"Slow database response: {database.response_time_ms}ms")
    
    # Check models
    models = check_model_health()
    
    for model_name, model_health in models.items():
        if not model_health.model_loaded:
            errors.append(f"Model not loaded: {model_name}")
    
    # Determine overall status
    if errors:
        overall_status = "unhealthy"
    elif warnings:
        overall_status = "degraded"
    else:
        overall_status = "healthy"
    
    # Calculate uptime
    uptime = (datetime.utcnow() - APP_START_TIME).total_seconds()
    
    return DetailedHealthResponse(
        overall_status=overall_status,
        timestamp=datetime.utcnow(),
        uptime_seconds=uptime,
        version="2.0.0",
        system=system,
        database=database,
        models=models,
        warnings=warnings,
        errors=errors
    )


@router.get("/metrics")
async def prometheus_metrics():
    """
    Prometheus-compatible metrics endpoint.
    
    Returns metrics in Prometheus exposition format:
    https://prometheus.io/docs/instrumenting/exposition_formats/
    """
    system = check_system_health()
    uptime = (datetime.utcnow() - APP_START_TIME).total_seconds()
    
    metrics = f"""# HELP radikal_cpu_usage_percent CPU usage percentage
# TYPE radikal_cpu_usage_percent gauge
radikal_cpu_usage_percent {system.cpu_percent}

# HELP radikal_memory_usage_percent Memory usage percentage
# TYPE radikal_memory_usage_percent gauge
radikal_memory_usage_percent {system.memory_percent}

# HELP radikal_disk_usage_percent Disk usage percentage
# TYPE radikal_disk_usage_percent gauge
radikal_disk_usage_percent {system.disk_percent}

# HELP radikal_gpu_available GPU availability
# TYPE radikal_gpu_available gauge
radikal_gpu_available {1 if system.gpu_available else 0}

# HELP radikal_uptime_seconds Application uptime in seconds
# TYPE radikal_uptime_seconds counter
radikal_uptime_seconds {uptime}
"""
    
    if system.gpu_memory_used is not None:
        metrics += f"""
# HELP radikal_gpu_memory_used_gb GPU memory used in GB
# TYPE radikal_gpu_memory_used_gb gauge
radikal_gpu_memory_used_gb {system.gpu_memory_used}

# HELP radikal_gpu_memory_total_gb GPU total memory in GB
# TYPE radikal_gpu_memory_total_gb gauge
radikal_gpu_memory_total_gb {system.gpu_memory_total}
"""
    
    return metrics


@router.get("/ready")
async def readiness_check(db: Session = Depends(get_db)):
    """
    Kubernetes readiness probe.
    
    Returns 200 if service is ready to accept traffic:
    - Database is connected
    - Models are loaded
    """
    # Check database
    database = await check_database_health(db)
    if not database.connected:
        return {"ready": False, "reason": "Database not connected"}, 503
    
    # Check models
    models = check_model_health()
    if not any(m.model_loaded for m in models.values()):
        return {"ready": False, "reason": "No models loaded"}, 503
    
    return {"ready": True}


@router.get("/live")
async def liveness_check():
    """
    Kubernetes liveness probe.
    
    Returns 200 if service is alive (not deadlocked).
    """
    # Simple check - if we can respond, we're alive
    return {"alive": True}
