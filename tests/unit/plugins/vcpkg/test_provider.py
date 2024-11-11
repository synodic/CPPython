"""Unit test the provider plugin"""

from typing import Any

import pytest

from cppython.plugins.vcpkg.plugin import VcpkgProvider
from cppython.plugins.vcpkg.resolution import generate_manifest
from tests.plugin_helper.tests import ProviderUnitTests


class TestCPPythonProvider(ProviderUnitTests[VcpkgProvider]):
    """The tests for the vcpkg Provider"""

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

    def test_manifest_generation(self, data_plugin: VcpkgProvider) -> None:
        """Verifies that manifests can be generated from core data

        Args:
            data_plugin: Generated plugin
        """

        assert generate_manifest(data_plugin.core_data, data_plugin.data)
