"""Health check endpoints."""

from datetime import datetime
from typing import Dict

from fastapi import APIRouter, status
from pydantic import BaseModel

from src.core.config import settings


router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""
    
    status: str
    timestamp: datetime
    version: str
    environment: str
    services: Dict[str, str]


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Check the health status of the application and its dependencies",
)
async def health_check() -> HealthResponse:
    """Perform health check."""
    # In a real application, you would check database, redis, etc.
    services_status = {
        "api": "healthy",
        "database": "healthy",
        "redis": "healthy",
        "mcp_server": "healthy",
    }
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        services=services_status,
    )


@router.get(
    "/health/live",
    status_code=status.HTTP_200_OK,
    summary="Liveness probe",
    description="Kubernetes liveness probe endpoint",
)
async def liveness():
    """Liveness probe for Kubernetes."""
    return {"status": "alive"}


@router.get(
    "/health/ready",
    status_code=status.HTTP_200_OK,
    summary="Readiness probe",
    description="Kubernetes readiness probe endpoint",
)
async def readiness():
    """Readiness probe for Kubernetes."""
    # Check if the application is ready to serve traffic
    # In a real app, check database connections, etc.
    return {"status": "ready"}