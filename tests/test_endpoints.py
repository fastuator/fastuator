"""Test basic Fastuator endpoints."""
from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient):
    """Test health check endpoint returns UP status."""
    response = client.get("/fastuator/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "UP"


def test_liveness_endpoint(client: TestClient):
    """Test liveness probe endpoint."""
    response = client.get("/fastuator/liveness")
    assert response.status_code == 200
    assert response.json()["status"] == "UP"


def test_readiness_endpoint(client: TestClient):
    """Test readiness probe endpoint."""
    response = client.get("/fastuator/readiness")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] in ["UP", "DOWN"]


def test_info_endpoint(client: TestClient):
    """Test system info endpoint."""
    response = client.get("/fastuator/info")
    assert response.status_code == 200

    data = response.json()
    # 실제 응답 구조에 맞춤
    assert "build" in data
    assert "system" in data
    assert "version" in data["build"]
    assert "python" in data["build"]
    assert "platform" in data["system"]


def test_metrics_endpoint(client: TestClient):
    """Test Prometheus metrics endpoint."""
    response = client.get("/fastuator/metrics")
    assert response.status_code == 200

    assert "text/plain" in response.headers["content-type"]

    content = response.text
    assert len(content) > 0
