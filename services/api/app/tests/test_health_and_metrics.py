import pytest
from fastapi.testclient import TestClient

# Import the FastAPI app
from app.main_bubblegrade import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "healthy"

def test_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    content_type = response.headers.get("content-type", "")
    assert content_type.startswith("text/plain")
    text = response.text
    # Ensure Prometheus metric counter is present
    assert "http_requests_total" in text