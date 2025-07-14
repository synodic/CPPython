"""Integration tests for the provider"""

from pathlib import Path
from typing import Any

import pytest

from cppython.plugins.conan.plugin import ConanProvider
from cppython.test.pytest.contracts import ProviderIntegrationTestContract


@pytest.fixture(autouse=True)
def clean_conan_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Sets CONAN_HOME to a temporary directory for each test.

    This ensures all tests run with a clean Conan cache.

    Args:
        tmp_path: Pytest temporary directory fixture
        monkeypatch: Pytest monkeypatch fixture for environment variable manipulation
    """
    conan_home = tmp_path / 'conan_home'
    conan_home.mkdir()

    # Set CONAN_HOME to the temporary directory
    monkeypatch.setenv('CONAN_HOME', str(conan_home))


class TestConanProvider(ProviderIntegrationTestContract[ConanProvider]):
    """The tests for the conan provider"""

    @staticmethod
    @pytest.fixture(name='plugin_data', scope='session')
    def fixture_plugin_data() -> dict[str, Any]:
        """A required testing hook that allows data generation

        Returns:
            The constructed plugin data
        """
        return {}

    @staticmethod
    @pytest.fixture(name='plugin_type', scope='session')
    def fixture_plugin_type() -> type[ConanProvider]:
        """A required testing hook that allows type generation

        Returns:
            The type of the Provider
        """
        return ConanProvider
