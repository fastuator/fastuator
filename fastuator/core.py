"""
Core implementation of Fastuator monitoring toolkit.

This module provides the main Fastuator class that automatically registers
health check, metrics, and info endpoints for FastAPI applications.
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable
import asyncio
import time
import importlib.metadata
import platform

from fastapi import APIRouter, FastAPI, HTTPException, Request
from prometheus_client import Counter, Gauge, Histogram, make_asgi_app, REGISTRY
import psutil


def get_package_version() -> str:
    """Get package version dynamically."""
    try:
        return importlib.metadata.version("fastuator")
    except importlib.metadata.PackageNotFoundError:
        return "dev"


class Fastuator:
    """
    Production-ready monitoring toolkit for FastAPI applications.

    Fastuator automatically registers the following endpoints:
    - /fastuator/health: Aggregated health check with optional details
    - /fastuator/liveness: Kubernetes liveness probe
    - /fastuator/readiness: Kubernetes readiness probe
    - /fastuator/info: Build and system information
    - /fastuator/metrics: Prometheus metrics (optional)

    The health check aggregation follows the Spring Boot Actuator pattern:
    if any component is DOWN, the overall status is DOWN.

    Example:
        >>> from fastapi import FastAPI
        >>> from fastuator import Fastuator
        >>>
        >>> app = FastAPI()
        >>> Fastuator(app)  # Registers all fastuator endpoints
        >>>
        >>> # With custom health checks
        >>> async def redis_health():
        ...     return {"status": "UP", "redis": "connected"}
        >>>
        >>> Fastuator(app, health_checks=[redis_health])

    Args:
        app: FastAPI application instance
        prefix: URL prefix for fastuator endpoints (default: "/fastuator")
        health_checks: Custom health check functions (async callables)
        liveness_checks: Health checks for K8s liveness probe (default: CPU only)
        readiness_checks: Health checks for K8s readiness probe (default: all checks)
        enable_metrics: Enable Prometheus metrics collection (default: True)
    """

    def __init__(
        self,
        app: FastAPI,
        prefix: str = "/fastuator",
        health_checks: list[Callable[[], Awaitable[dict[str, Any]]]] | None = None,
        liveness_checks: list[Callable[[], Awaitable[dict[str, Any]]]] | None = None,
        readiness_checks: list[Callable[[], Awaitable[dict[str, Any]]]] | None = None,
        enable_metrics: bool = True,
    ) -> None:
        self.app = app
        self.prefix = prefix
        self.router = APIRouter(prefix=prefix, tags=["fastuator"])

        # Import default health checks
        from .checks import cpu_health, disk_health, memory_health

        # Configure health check functions
        self.health_checks = health_checks or [cpu_health, disk_health, memory_health]
        self.liveness_checks = liveness_checks or [cpu_health]
        self.readiness_checks = readiness_checks or self.health_checks

        use_test_registry = False
        test_registry = None
        if "pytest" in [m.__name__ for m in __import__("sys").modules.values()]:
            from prometheus_client import CollectorRegistry

            test_registry = CollectorRegistry()
            use_test_registry = True

        self.request_count = Counter(
            "http_requests_total",
            "Total HTTP requests",
            ["method", "endpoint", "status"],
            registry=test_registry if use_test_registry else REGISTRY,
        )
        self.request_duration = Histogram(
            "http_request_duration_seconds",
            "HTTP request duration in seconds",
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
            registry=test_registry if use_test_registry else REGISTRY,
        )
        self.health_status = Gauge(
            "app_health_status",
            "Application health status (1=UP, 0=DOWN)",
            registry=test_registry if use_test_registry else REGISTRY,
        )

        # Setup endpoints
        self._register_health_endpoints()

        # Setup Prometheus metrics if enabled
        if enable_metrics:
            self._register_metrics_endpoint(app, prefix)
            self._register_metrics_middleware(app)

        # Register router with FastAPI app
        app.include_router(self.router)

    def _register_health_endpoints(self) -> None:
        """Register health check, liveness, readiness, and info endpoints."""

        @self.router.get("/health")
        async def health(show_details: bool = False) -> dict[str, Any]:
            """
            Aggregate health check endpoint.

            Returns overall status based on all registered health checks.
            If any check returns DOWN, the overall status is DOWN.

            Query Parameters:
                show_details: Include detailed component status (default: False)

            Returns:
                {"status": "UP"} or {"status": "DOWN", "components": {...}}
            """
            checks = await asyncio.gather(
                *[asyncio.wait_for(check(), timeout=5.0) for check in self.health_checks],
                return_exceptions=True,
            )

            # Handle exceptions in health checks
            processed_checks = []
            for i, check_result in enumerate(checks):
                if isinstance(check_result, Exception):
                    processed_checks.append(
                        {
                            "status": "DOWN",
                            "error": str(check_result),
                        }
                    )
                else:
                    processed_checks.append(check_result)

            # Aggregate status: DOWN if any component is DOWN
            statuses = [c.get("status", "DOWN") for c in processed_checks]
            overall_status = "DOWN" if "DOWN" in statuses else "UP"

            # Update Prometheus gauge
            self.health_status.set(1 if overall_status == "UP" else 0)

            result = {"status": overall_status}
            if show_details:
                result["components"] = {
                    getattr(check, "__name__", f"check_{i}"): check_result
                    for i, (check, check_result) in enumerate(
                        zip(self.health_checks, processed_checks)
                    )
                }

            return result

        @self.router.get("/liveness")
        async def liveness() -> dict[str, str]:
            """
            Kubernetes liveness probe endpoint.

            Checks only critical system components (e.g., CPU).
            Returns 503 if any liveness check fails.

            This follows the isolation pattern: external dependencies
            (DB, Redis) should not affect liveness to prevent cascading failures.

            Returns:
                {"status": "UP"} or raises HTTPException(503)
            """
            checks = await asyncio.gather(
                *[asyncio.wait_for(check(), timeout=5.0) for check in self.liveness_checks],
                return_exceptions=True,
            )

            for check_result in checks:
                if isinstance(check_result, Exception) or check_result.get("status") != "UP":
                    raise HTTPException(
                        status_code=503,
                        detail="Liveness check failed",
                    )

            return {"status": "UP"}

        @self.router.get("/readiness")
        async def readiness() -> dict[str, str]:
            """
            Kubernetes readiness probe endpoint.

            Checks all dependencies including external services.
            Returns 503 if any readiness check fails.

            Returns:
                {"status": "UP"} or raises HTTPException(503)
            """
            checks = await asyncio.gather(
                *[asyncio.wait_for(check(), timeout=5.0) for check in self.readiness_checks],
                return_exceptions=True,
            )

            for check_result in checks:
                if isinstance(check_result, Exception) or check_result.get("status") != "UP":
                    raise HTTPException(
                        status_code=503,
                        detail="Readiness check failed",
                    )

            return {"status": "UP"}

        @self.router.get("/info")
        async def info() -> dict[str, Any]:
            """
            Application and system information endpoint.

            Returns build version, Python version, and platform details.

            Returns:
                Dictionary with build and system information
            """
            return {
                "build": {
                    "version": get_package_version(),
                    "python": platform.python_version(),
                },
                "system": {
                    "platform": platform.platform(),
                    "python_implementation": platform.python_implementation(),
                },
            }

    def _register_metrics_endpoint(self, app: FastAPI, prefix: str) -> None:
        """
        Mount Prometheus metrics endpoint.

        Args:
            app: FastAPI application instance
            prefix: Fastuator URL prefix
        """
        metrics_app = make_asgi_app()
        app.mount(f"{prefix}/metrics", metrics_app)

    def _register_metrics_middleware(self, app: FastAPI) -> None:
        """
        Register middleware for automatic metrics collection.

        Collects HTTP request count and duration for all endpoints.

        Args:
            app: FastAPI application instance
        """

        if hasattr(app.state, "_fastuator_metrics_middleware"):
            return
        app.state._fastuator_metrics_middleware = True

        @app.middleware("http")
        async def metrics_middleware(request: Request, call_next):
            """Collect HTTP request metrics."""
            start_time = time.time()

            # Process request
            response = await call_next(request)

            # Record metrics
            duration = time.time() - start_time
            self.request_count.labels(
                method=request.method,
                endpoint=request.url.path,
                status=response.status_code,
            ).inc()
            self.request_duration.observe(duration)

            return response
