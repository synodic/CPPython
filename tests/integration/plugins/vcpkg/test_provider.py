"""Integration tests for the provider"""

from typing import Any

import pytest

from cppython.plugins.vcpkg.plugin import VcpkgProvider
from cppython.test.pytest.contracts import ProviderIntegrationTestContract


class TestCPPythonProvider(ProviderIntegrationTestContract[VcpkgProvider]):
    """The tests for the vcpkg provider"""

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
    def fixture_plugin_type() -> type[VcpkgProvider]:
        """A required testing hook that allows type generation

        Returns:
            The type of the Provider
        """
        return VcpkgProvider
