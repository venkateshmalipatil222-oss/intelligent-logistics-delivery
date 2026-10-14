import os
import platform
import time
from datetime import datetime, timezone
from fastapi import APIRouter, Response, status
from backend.app.core.config import settings
from backend.app.core.database import check_db_connection

router = APIRouter()

APP_START_TIME = time.time()


@router.get("", summary="Comprehensive System & Dependency Health Status")
def get_health_status(response: Response):
    """
    Evaluates backend service health and performs a live check on required dependencies (MySQL).
    Returns 200 OK if all components are healthy, or 503 Service Unavailable if any critical
    dependency fails.
    """
    db_health = check_db_connection()
    uptime_seconds = round(time.time() - APP_START_TIME, 2)
    
    is_healthy = db_health.get("status") == "connected"
    
    if not is_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "uptime_seconds": uptime_seconds,
        "dependencies": {
            "database": db_health
        },
        "system": {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "process_id": os.getpid(),
        }
    }


@router.get("/ping", summary="Lightweight Liveness Ping")
def ping():
    """
    Fast endpoint for load-balancers or container liveness probes.
    """
    return {
        "ping": "pong",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
