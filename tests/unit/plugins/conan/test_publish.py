"""Unit tests for the conan plugin publish functionality"""

from typing import Any

import pytest

from cppython.plugins.conan.plugin import ConanProvider
from cppython.test.pytest.mixins import ProviderPluginTestMixin

# Use shared fixtures
pytest_plugins = ['tests.fixtures.conan']


class TestConanPublish(ProviderPluginTestMixin[ConanProvider]):
    """Tests for the Conan provider publish functionality"""

    @staticmethod
    @pytest.fixture(name='plugin_data', scope='session')
    def fixture_plugin_data() -> dict[str, Any]:
        """A required testing hook that allows data generation

        Returns:
            The constructed plugin data
        """
        return {
            'remotes': ['conancenter'],
        }

    @staticmethod
    @pytest.fixture(name='plugin_type', scope='session')
    def fixture_plugin_type() -> type[ConanProvider]:
        """A required testing hook that allows type generation

        Returns:
            The type of the Provider
        """
        return ConanProvider
