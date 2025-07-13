"""Unit tests for the conan plugin update functionality

This module tests the update-specific behavior and differences from install.
The core installation functionality is tested in test_install.py since both
install() and update() now share the same underlying implementation.
"""

from typing import Any

import pytest

from cppython.plugins.conan.plugin import ConanProvider
from cppython.test.pytest.mixins import ProviderPluginTestMixin

pytest_plugins = ['tests.fixtures.conan']


class TestConanUpdate(ProviderPluginTestMixin[ConanProvider]):
    """Tests for the Conan provider update-specific functionality"""

    @staticmethod
    @pytest.fixture(name='plugin_data', scope='session')
    def fixture_plugin_data() -> dict[str, Any]:
        """A required testing hook that allows data generation

        Returns:
            The constructed plugin data
        """
        return {
            'remotes': [],
        }

    @staticmethod
    @pytest.fixture(name='plugin_type', scope='session')
    def fixture_plugin_type() -> type[ConanProvider]:
        """A required testing hook that allows type generation

        Returns:
            The type of the Provider
        """
        return ConanProvider
