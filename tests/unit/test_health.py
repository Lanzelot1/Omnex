"""Test health endpoints."""

import pytest
from fastapi import status


def test_health_check(client):
    """Test the main health check endpoint."""
    response = client.get("/health")
    
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert data["version"] == "0.1.0"
    assert data["environment"] == "development"
    assert "services" in data
    assert data["services"]["api"] == "healthy"


def test_liveness_probe(client):
    """Test the Kubernetes liveness probe endpoint."""
    response = client.get("/health/live")
    
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "alive"}


def test_readiness_probe(client):
    """Test the Kubernetes readiness probe endpoint."""
    response = client.get("/health/ready")
    
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ready"}