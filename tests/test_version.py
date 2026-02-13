"""Test dynamic version detection."""

import pytest
import importlib.metadata
from unittest.mock import patch
from fastuator.core import get_package_version


def test_dev_mode_fallback():
    """Test dev version when package not installed."""
    with patch("importlib.metadata.version") as mock_version:
        mock_version.side_effect = importlib.metadata.PackageNotFoundError

        version = get_package_version()
        assert version == "dev"


def test_installed_version():
    """Test installed version detection."""
    with patch("importlib.metadata.version") as mock_version:
        mock_version.return_value = "0.0.1"

        version = get_package_version()
        assert version == "0.0.1"


@pytest.mark.parametrize("version", ["0.0.1", "1.2.3-dev", "dev"])
def test_version_format(version):
    """Test version returns string."""
    with patch("importlib.metadata.version") as mock_version:
        mock_version.return_value = version

        result = get_package_version()
        assert isinstance(result, str)
        assert result == version or result == "dev"
