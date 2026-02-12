"""
fastuator - Production-ready monitoring for FastAPI
K8s probes, Prometheus metrics, health checks in 1 line.
"""

__version__ = "0.0.1"

from .core import Fastuator
from .checks import cpu_health, disk_health, memory_health

__all__ = ["Fastuator", "cpu_health", "disk_health", "memory_health"]
