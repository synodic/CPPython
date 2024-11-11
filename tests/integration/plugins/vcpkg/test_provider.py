"""Integration tests for the provider"""

from typing import Any

import pytest

from cppython.plugins.vcpkg.plugin import VcpkgProvider
from tests.plugin_helper.tests import ProviderIntegrationTests


class TestCPPythonProvider(ProviderIntegrationTests[VcpkgProvider]):
    """The tests for the vcpkg provider"""

    @pytest.fixture(name="plugin_data", scope="session")
    def fixture_plugin_data(self) -> dict[str, Any]:
        """A required testing hook that allows data generation

        Returns:
            The constructed plugin data
        """
        return {}

    @pytest.fixture(name="plugin_type", scope="session")
    def fixture_plugin_type(self) -> type[VcpkgProvider]:
        """A required testing hook that allows type generation

        Returns:
            The type of the Provider
        """
        return VcpkgProvider
