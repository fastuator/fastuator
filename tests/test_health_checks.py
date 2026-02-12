"""Test health check implementations."""

import pytest
from fastuator.checks import cpu_health, memory_health, disk_health


@pytest.mark.asyncio
async def test_cpu_health():
    """Test CPU health check returns correct format."""
    result = await cpu_health()

    assert "status" in result
    assert result["status"] in ["UP", "DOWN"]
    assert "cpu_percent" in result
    assert isinstance(result["cpu_percent"], (int, float))
    assert 0 <= result["cpu_percent"] <= 100


@pytest.mark.asyncio
async def test_memory_health():
    """Test memory health check returns correct format."""
    result = await memory_health()

    assert "status" in result
    assert result["status"] in ["UP", "DOWN"]
    assert "memory_percent" in result
    assert "memory_available_mb" in result
    assert isinstance(result["memory_percent"], (int, float))
    assert isinstance(result["memory_available_mb"], int)
    assert 0 <= result["memory_percent"] <= 100
    assert result["memory_available_mb"] >= 0


@pytest.mark.asyncio
async def test_disk_health():
    """Test disk health check returns correct format."""
    result = await disk_health()

    assert "status" in result
    assert result["status"] in ["UP", "DOWN"]
    assert "disk_percent" in result
    assert "disk_free_gb" in result
    assert isinstance(result["disk_percent"], (int, float))
    assert isinstance(result["disk_free_gb"], int)
    assert 0 <= result["disk_percent"] <= 100
    assert result["disk_free_gb"] >= 0


@pytest.mark.asyncio
async def test_cpu_health_status_logic():
    """Test CPU health returns DOWN when usage is high."""
    result = await cpu_health()

    if result["cpu_percent"] < 90:
        assert result["status"] == "UP"
    else:
        assert result["status"] == "DOWN"


@pytest.mark.asyncio
async def test_memory_health_status_logic():
    """Test memory health returns DOWN when usage is high."""
    result = await memory_health()

    if result["memory_percent"] < 90:
        assert result["status"] == "UP"
    else:
        assert result["status"] == "DOWN"


@pytest.mark.asyncio
async def test_disk_health_status_logic():
    """Test disk health returns DOWN when usage is high."""
    result = await disk_health()

    if result["disk_percent"] < 90:
        assert result["status"] == "UP"
    else:
        assert result["status"] == "DOWN"
