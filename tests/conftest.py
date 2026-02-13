"""Test configuration and fixtures."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastuator import Fastuator
import asyncio


@pytest.fixture
def client():
    """Create a test client with default health checks.

    Uses real CPU/memory/disk checks - may fail if system resources are high.
    """
    app = FastAPI()
    Fastuator(app)
    Fastuator(app)  # v0.1.0: duplicate prevention test

    # Verify v0.1.0 duplicate prevention
    assert len(app.user_middleware) == 1
    assert hasattr(app.state, "_fastuator_metrics_middleware")

    return TestClient(app)


@pytest.fixture
def success_client():
    """Create a test client with always-passing checks.

    Guarantees 200 OK responses for testing happy paths.
    """
    app = FastAPI()

    async def passing_check():
        return {"status": "UP"}

    Fastuator(
        app,
        health_checks=[passing_check],
        readiness_checks=[passing_check],
        liveness_checks=[passing_check],
    )

    return TestClient(app)


@pytest.fixture
def failing_client():
    """Create a test client with always-failing checks.

    Returns DOWN status without exceptions.
    """
    app = FastAPI()

    async def failing_check():
        return {"status": "DOWN", "reason": "Test failure"}

    Fastuator(
        app,
        health_checks=[failing_check],
        readiness_checks=[failing_check],
        liveness_checks=[failing_check],
    )

    return TestClient(app)


@pytest.fixture
def exception_client():
    """Create a test client with exception-raising health checks.

    Tests exception handling in health endpoint (line 128 in core.py).
    """
    app = FastAPI()

    async def exception_check():
        raise RuntimeError("Database connection failed")

    Fastuator(app, health_checks=[exception_check])

    return TestClient(app)


@pytest.fixture
def exception_readiness_client():
    """Create a test client with exception-raising readiness checks.

    Tests exception handling in readiness endpoint (line 207 in core.py).
    """
    app = FastAPI()

    async def exception_check():
        raise RuntimeError("Service unavailable")

    Fastuator(app, readiness_checks=[exception_check])

    return TestClient(app)


def test_v010_duplicate_prevention():
    """Test v0.1.0: No duplicate middleware registration."""
    app = FastAPI()

    Fastuator(app)  # First
    count1 = len(app.user_middleware)

    Fastuator(app)  # Second (skipped)
    count2 = len(app.user_middleware)

    assert count1 == count2
    assert hasattr(app.state, "_fastuator_metrics_middleware")


def test_v010_readable_check_names(client):
    """Test v0.1.0: Health details show readable check names."""
    response = client.get("/fastuator/health?show_details=true")
    assert response.status_code == 200

    components = response.json()["components"]
    assert "cpu_health" in components
    assert "check_0" not in components


def test_v010_dynamic_version():
    """Test v0.1.0: Dynamic package version."""
    app = FastAPI()
    Fastuator(app)
    client = TestClient(app)

    info = client.get("/fastuator/info").json()
    version = info["build"]["version"]
    assert version in ["dev", "0.1.0"]


def test_v010_health_timeout():
    """Test v0.1.0: 5s timeout protection."""
    app = FastAPI()

    async def slow_check():
        await asyncio.sleep(10)
        return {"status": "UP"}

    Fastuator(app, health_checks=[slow_check])
    client = TestClient(app)

    response = client.get("/fastuator/health")
    assert response.status_code == 200
    assert response.json()["status"] == "DOWN"
