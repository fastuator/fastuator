"""Test basic Fastuator endpoints."""

from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient):
    """Test health check endpoint returns UP status."""
    response = client.get("/fastuator/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] in ["UP", "DOWN"]


def test_liveness_endpoint(success_client: TestClient):
    """Test liveness probe endpoint."""
    response = success_client.get("/fastuator/liveness")
    assert response.status_code == 200
    assert response.json()["status"] == "UP"


def test_readiness_endpoint_flexible(client: TestClient):
    """Test readiness with real health checks (may vary)."""
    response = client.get("/fastuator/readiness")
    assert response.status_code in [200, 503]

    if response.status_code == 200:
        assert response.json() == {"status": "UP"}
    else:
        assert "detail" in response.json()


def test_readiness_success(success_client: TestClient):
    """Test readiness returns UP when all checks pass."""
    response = success_client.get("/fastuator/readiness")
    assert response.status_code == 200
    assert response.json() == {"status": "UP"}


def test_info_endpoint(client: TestClient):
    """Test system info endpoint."""
    response = client.get("/fastuator/info")
    assert response.status_code == 200

    data = response.json()

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


def test_health_with_details(client: TestClient):
    """Test health endpoint with show_details parameter."""
    response = client.get("/fastuator/health?show_details=true")
    assert response.status_code in [200, 503]

    data = response.json()
    assert "status" in data
    assert "components" in data
    assert isinstance(data["components"], dict)


def test_health_with_exception(exception_client: TestClient):
    """Test health endpoint handles exceptions from checks."""
    response = exception_client.get("/fastuator/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "DOWN"


def test_health_with_exception_details(exception_client: TestClient):
    """Test health endpoint captures exception in components when show_details=true."""
    response = exception_client.get("/fastuator/health?show_details=true")

    data = response.json()
    assert "components" in data
    components = data["components"]
    assert any("error" in comp for comp in components.values())


def test_failing_liveness(failing_client: TestClient):
    """Test liveness with failing check returns 503."""
    response = failing_client.get("/fastuator/liveness")
    assert response.status_code == 503

    data = response.json()
    assert "detail" in data


def test_failing_readiness(failing_client: TestClient):
    """Test readiness with failing check returns 503."""
    response = failing_client.get("/fastuator/readiness")
    assert response.status_code == 503

    data = response.json()
    assert "detail" in data


def test_readiness_with_exception(exception_readiness_client: TestClient):
    """Test readiness with exception returns 503."""
    response = exception_readiness_client.get("/fastuator/readiness")
    assert response.status_code == 503

    data = response.json()
    assert "detail" in data
