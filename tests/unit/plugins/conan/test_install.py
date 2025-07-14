"""Unit tests for the conan plugin install functionality"""

from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest
from packaging.requirements import Requirement
from pytest_mock import MockerFixture

from cppython.plugins.conan.plugin import ConanProvider
from cppython.plugins.conan.schema import ConanDependency
from cppython.test.pytest.mixins import ProviderPluginTestMixin
from cppython.utility.exception import ProviderInstallationError

# Use shared fixtures
pytest_plugins = ['tests.fixtures.conan']

# Constants for test verification
EXPECTED_DEPENDENCY_COUNT = 2
EXPECTED_PROFILE_CALLS = 2


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

    def test_install_with_dependencies(
        self,
        plugin: ConanProvider,
        conan_temp_conanfile: Path,
        conan_mock_dependencies: list[Requirement],
        conan_setup_mocks: dict[str, Mock],
    ) -> None:
        """Test install method with dependencies and existing conanfile

        Args:
            plugin: The plugin instance
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

        # Verify ConanAPI constructor was called
        conan_setup_mocks['conan_api_constructor'].assert_called_once()

    def test_install_conan_command_failure(
        self,
        plugin: ConanProvider,
        conan_temp_conanfile: Path,
        conan_mock_dependencies: list[Requirement],
        conan_mock_api: Mock,
        mocker: MockerFixture,
    ) -> None:
        """Test install method when conan API operations fail

        Args:
            plugin: The plugin instance
            conan_temp_conanfile: Path to temporary conanfile.py
            conan_mock_dependencies: List of mock dependencies
            conan_mock_api: Mock ConanAPI instance
            mocker: Pytest mocker fixture
        """
        # Mock builder
        mock_builder = mocker.Mock()
        mock_builder.generate_conanfile = mocker.Mock()
        plugin.builder = mock_builder  # type: ignore[attr-defined]

        # Configure the API mock to fail on graph loading
        conan_mock_api.graph.load_graph_consumer.side_effect = Exception('Conan API error: package not found')
        
        # Mock ConanAPI constructor to return our configured mock
        mock_conan_api_constructor = mocker.patch('cppython.plugins.conan.plugin.ConanAPI', return_value=conan_mock_api)

        # Mock resolve_conan_dependency
        def mock_resolve(requirement: Requirement) -> ConanDependency:
            return ConanDependency(name=requirement.name, version_ge=None)

        mocker.patch('cppython.plugins.conan.plugin.resolve_conan_dependency', side_effect=mock_resolve)

        # Add a dependency
        plugin.core_data.cppython_data.dependencies = [conan_mock_dependencies[0]]

        # Execute and verify exception is raised
        with pytest.raises(
            ProviderInstallationError, 
            match='Failed to install dependencies: Conan API error: package not found'
        ):
            plugin.install()

        # Verify builder was still called
        mock_builder.generate_conanfile.assert_called_once()

        # Verify Conan API was attempted
        mock_conan_api_constructor.assert_called_once()

    def test_install_with_profile_exception_fallback(
        self,
        plugin: ConanProvider,
        conan_temp_conanfile: Path,
        conan_mock_dependencies: list[Requirement],
        conan_setup_mocks: dict[str, Mock],
        conan_mock_api: Mock,
    ) -> None:
        """Test install method when profile operations throw exceptions

        Args:
            plugin: The plugin instance
            conan_temp_conanfile: Path to temporary conanfile.py
            conan_mock_dependencies: List of mock dependencies
            conan_setup_mocks: Dictionary containing all mocks
            conan_mock_api: Mock ConanAPI instance
        """
        # Configure the API mock to throw exception on first profile call
        conan_mock_api.profiles.get_default_host.side_effect = Exception('Profile not found')

        # Setup dependencies
        plugin.core_data.cppython_data.dependencies = conan_mock_dependencies

        # Execute - should not throw an exception despite profile operations failing
        plugin.install()

        # Verify that despite the exceptions, the fallback was used
        conan_setup_mocks['conan_api_constructor'].assert_called_once()
        conan_mock_api.profiles.get_default_host.assert_called_once()
        # Note: get_default_build is not called because get_default_host throws exception first
        
        # Verify fallback profile creation was called (should be called twice for empty profiles)
        assert conan_mock_api.profiles.get_profile.call_count >= EXPECTED_PROFILE_CALLS
        
        # Verify the rest of the process continued
        conan_mock_api.graph.load_graph_consumer.assert_called_once()
        conan_mock_api.install.install_binaries.assert_called_once()
        conan_mock_api.install.install_consumer.assert_called_once()

    def test_publish_with_profile_exception_fallback(
        self,
        plugin: ConanProvider,
        conan_temp_conanfile: Path,
        conan_mock_api_publish: Mock,
        mocker: MockerFixture,
    ) -> None:
        """Test publish method when profile operations throw exceptions

        Args:
            plugin: The plugin instance
            conan_temp_conanfile: Path to temporary conanfile.py
            conan_mock_api_publish: Mock ConanAPI instance configured for publish
            mocker: Pytest mocker fixture
        """
        # Set plugin to local mode to avoid remote upload complications
        plugin.data = plugin.data.__class__(
            remotes=[],
        )

        # Configure the API mock to throw exception on first profile call
        conan_mock_api_publish.profiles.get_default_host.side_effect = Exception('Profile configuration error')
        
        # Mock ConanAPI constructor to return our configured mock
        mock_conan_api_constructor = mocker.patch(
            'cppython.plugins.conan.plugin.ConanAPI', return_value=conan_mock_api_publish
        )

        # Execute - should not throw an exception despite profile operations failing
        plugin.publish()

        # Verify that despite the exceptions, the fallback was used
        mock_conan_api_constructor.assert_called_once()
        conan_mock_api_publish.profiles.get_default_host.assert_called_once()
        # Note: get_default_build is not called because get_default_host throws exception first
        
        # Verify fallback profile creation was called (should be called twice for empty profiles)
        assert conan_mock_api_publish.profiles.get_profile.call_count >= EXPECTED_PROFILE_CALLS
        
        # Verify the rest of the process continued
        conan_mock_api_publish.export.export.assert_called_once()
        conan_mock_api_publish.graph.load_graph_consumer.assert_called_once()
        conan_mock_api_publish.install.install_binaries.assert_called_once()

    def test_install_with_second_profile_exception_fallback(
        self,
        plugin: ConanProvider,
        conan_temp_conanfile: Path,
        conan_mock_dependencies: list[Requirement],
        conan_setup_mocks: dict[str, Mock],
        conan_mock_api: Mock,
    ) -> None:
        """Test install method when the second profile operation throws exception

        Args:
            plugin: The plugin instance
            conan_temp_conanfile: Path to temporary conanfile.py
            conan_mock_dependencies: List of mock dependencies
            conan_setup_mocks: Dictionary containing all mocks
            conan_mock_api: Mock ConanAPI instance
        """
        # Configure the API mock: first call succeeds, second one fails
        conan_mock_api.profiles.get_default_host.return_value = '/path/to/host'
        conan_mock_api.profiles.get_default_build.side_effect = Exception('Build profile not found')

        # Setup dependencies
        plugin.core_data.cppython_data.dependencies = conan_mock_dependencies

        # Execute - should not throw an exception despite profile operations failing
        plugin.install()

        # Verify that despite the exceptions, the fallback was used
        conan_setup_mocks['conan_api_constructor'].assert_called_once()
        conan_mock_api.profiles.get_default_host.assert_called_once()
        conan_mock_api.profiles.get_default_build.assert_called_once()
        
        # Verify fallback profile creation was called (should be called twice for empty profiles)
        assert conan_mock_api.profiles.get_profile.call_count >= EXPECTED_PROFILE_CALLS
        
        # Verify the rest of the process continued
        conan_mock_api.graph.load_graph_consumer.assert_called_once()
        conan_mock_api.install.install_binaries.assert_called_once()
        conan_mock_api.install.install_consumer.assert_called_once()
