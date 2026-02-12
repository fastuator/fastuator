"""Test configuration and fixtures."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastuator import Fastuator


@pytest.fixture
def client():
    """Create a test client with default health checks.

    Uses real CPU/memory/disk checks - may fail if system resources are high.
    """
    app = FastAPI()
    Fastuator(app)
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
