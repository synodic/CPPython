"""Unit tests for the conan plugin install functionality"""

from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest
from packaging.requirements import Requirement

from cppython.plugins.conan.plugin import ConanProvider
from cppython.test.pytest.mixins import ProviderPluginTestMixin

# Use shared fixtures
pytest_plugins = ['tests.fixtures.conan']

# Constants for test verification
EXPECTED_DEPENDENCY_COUNT = 2


class TestConanInstall(ProviderPluginTestMixin[ConanProvider]):
    """Tests for the Conan provider install functionality"""

    @staticmethod
    @pytest.fixture(name='plugin_data', scope='session')
    def fixture_plugin_data() -> dict[str, Any]:
        """A required testing hook that allows data generation

        Returns:
            The constructed plugin data
        """
        return {
            'local': True,
        }

    @staticmethod
    @pytest.fixture(name='plugin_type', scope='session')
    def fixture_plugin_type() -> type[ConanProvider]:
        """A required testing hook that allows type generation

        Returns:
            The type of the Provider
        """
        return ConanProvider

    def test_install_with_dependencies(
        self,
        plugin: ConanProvider,
        conan_mock_api: Mock,
        conan_temp_conanfile: Path,
        conan_mock_dependencies: list[Requirement],
        conan_setup_mocks: dict[str, Mock],
    ) -> None:
        """Test install method with dependencies and existing conanfile

        Args:
            plugin: The plugin instance
            conan_mock_api: Mock ConanAPI instance
            conan_temp_conanfile: Path to temporary conanfile.py
            conan_mock_dependencies: List of mock dependencies
            conan_setup_mocks: Dictionary containing all mocks
        """
        # Setup dependencies
        plugin.core_data.cppython_data.dependencies = conan_mock_dependencies

        # Execute
        plugin.install()

        # Verify builder was called
        conan_setup_mocks['builder'].generate_conanfile.assert_called_once()
        assert (
            conan_setup_mocks['builder'].generate_conanfile.call_args[0][0]
            == plugin.core_data.project_data.project_root
        )
        assert len(conan_setup_mocks['builder'].generate_conanfile.call_args[0][1]) == EXPECTED_DEPENDENCY_COUNT

        # Verify dependency resolution was called
        assert conan_setup_mocks['resolve_conan_dependency'].call_count == EXPECTED_DEPENDENCY_COUNT

        # Verify build path was created
        assert plugin.core_data.cppython_data.build_path.exists()

        # Verify Conan API calls
        conan_mock_api.profiles.get_default_host.assert_called_once()
        conan_mock_api.profiles.get_default_build.assert_called_once()
        conan_mock_api.profiles.get_profile.assert_called()
        conan_mock_api.graph.load_graph_consumer.assert_called_once()
        conan_mock_api.install.install_binaries.assert_called_once()

        # Verify graph consumer call arguments
        load_graph_args = conan_mock_api.graph.load_graph_consumer.call_args
        assert load_graph_args[1]['path'] == str(conan_temp_conanfile)
        assert load_graph_args[1]['update'] is False
        assert load_graph_args[1]['check_updates'] is False

    def test_install_without_conanfile(
        self,
        plugin: ConanProvider,
        conan_mock_api: Mock,
        conan_mock_dependencies: list[Requirement],
        conan_setup_mocks: dict[str, Mock],
    ) -> None:
        """Test install method when conanfile.py doesn't exist

        Args:
            plugin: The plugin instance
            conan_mock_api: Mock ConanAPI instance
            conan_mock_dependencies: List of mock dependencies
            conan_setup_mocks: Dictionary containing all mocks
        """
        # Setup dependencies
        plugin.core_data.cppython_data.dependencies = [conan_mock_dependencies[0]]

        # Execute
        plugin.install()

        # Verify builder was called
        conan_setup_mocks['builder'].generate_conanfile.assert_called_once()

        # Verify build path was created
        assert plugin.core_data.cppython_data.build_path.exists()

        # Verify Conan API calls were NOT made (no conanfile.py)
        conan_mock_api.profiles.get_default_host.assert_not_called()
        conan_mock_api.profiles.get_default_build.assert_not_called()
        conan_mock_api.profiles.get_profile.assert_not_called()
        conan_mock_api.graph.load_graph_consumer.assert_not_called()
        conan_mock_api.install.install_binaries.assert_not_called()

    def test_install_no_dependencies(
        self,
        plugin: ConanProvider,
        conan_mock_api: Mock,
        conan_temp_conanfile: Path,
        conan_setup_mocks: dict[str, Mock],
    ) -> None:
        """Test install method with no dependencies

        Args:
            plugin: The plugin instance
            conan_mock_api: Mock ConanAPI instance
            conan_temp_conanfile: Path to temporary conanfile.py
            conan_setup_mocks: Dictionary containing all mocks
        """
        # No dependencies
        plugin.core_data.cppython_data.dependencies = []

        # Execute
        plugin.install()

        # Verify builder was called with empty dependencies
        conan_setup_mocks['builder'].generate_conanfile.assert_called_once()
        assert len(conan_setup_mocks['builder'].generate_conanfile.call_args[0][1]) == 0

        # Verify dependency resolution was not called
        conan_setup_mocks['resolve_conan_dependency'].assert_not_called()

        # Verify build path was created
        assert plugin.core_data.cppython_data.build_path.exists()

        # Verify Conan API calls were still made (conanfile.py exists)
        conan_mock_api.profiles.get_default_host.assert_called_once()
        conan_mock_api.profiles.get_default_build.assert_called_once()
        conan_mock_api.profiles.get_profile.assert_called()
        conan_mock_api.graph.load_graph_consumer.assert_called_once()
        conan_mock_api.install.install_binaries.assert_called_once()

    def test_install_conan_api_failure(
        self,
        plugin: ConanProvider,
        conan_mock_api: Mock,
        conan_temp_conanfile: Path,
        conan_mock_dependencies: list[Requirement],
        conan_setup_mocks: dict[str, Mock],
    ) -> None:
        """Test install method when Conan API calls fail

        Args:
            plugin: The plugin instance
            conan_mock_api: Mock ConanAPI instance
            conan_temp_conanfile: Path to temporary conanfile.py
            conan_mock_dependencies: List of mock dependencies
            conan_setup_mocks: Dictionary containing all mocks
        """
        # Make API call fail
        conan_mock_api.graph.load_graph_consumer.side_effect = Exception('Conan graph load failed')

        # Add a dependency
        plugin.core_data.cppython_data.dependencies = [conan_mock_dependencies[0]]

        # Execute and verify exception is raised
        with pytest.raises(Exception, match='Conan graph load failed'):
            plugin.install()

        # Verify builder was still called
        conan_setup_mocks['builder'].generate_conanfile.assert_called_once()

        # Verify API was called up to the point of failure
        conan_mock_api.profiles.get_default_host.assert_called_once()
        conan_mock_api.profiles.get_default_build.assert_called_once()
        conan_mock_api.profiles.get_profile.assert_called()
        conan_mock_api.graph.load_graph_consumer.assert_called_once()
        conan_mock_api.install.install_binaries.assert_not_called()
