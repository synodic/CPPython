"""Unit test the provider plugin"""

from typing import Any

import pytest

from cppython.plugins.conan.plugin import ConanProvider
from cppython.test.pytest.contracts import ProviderUnitTestContract


class TestConanProvider(ProviderUnitTestContract[ConanProvider]):
    """The tests for the Conan Provider"""

    @staticmethod
    @pytest.fixture(name='plugin_data', scope='session')
    def fixture_plugin_data(conan_plugin_data: dict[str, Any]) -> dict[str, Any]:
        """A required testing hook that allows data generation

        Returns:
            The constructed plugin data
        """
        return conan_plugin_data

    @staticmethod
    @pytest.fixture(name='plugin_type', scope='session')
    def fixture_plugin_type() -> type[ConanProvider]:
        """A required testing hook that allows type generation

        Returns:
            The type of the Provider
        """
        return ConanProvider
