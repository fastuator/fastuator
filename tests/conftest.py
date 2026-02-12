import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastuator import Fastuator


@pytest.fixture
def app():
    """Create a basic FastAPI app for testing."""
    app = FastAPI()

    @app.get("/test")
    def test_endpoint():
        return {"message": "test"}

    return app


@pytest.fixture
def client(app):
    """Create a TestClient with Fastuator endpoints."""
    Fastuator(app)
    return TestClient(app)
