"""Unit tests for the conan plugin install functionality"""

import subprocess
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


class TestConanInstall(ProviderPluginTestMixin[ConanProvider]):
    """Tests for the Conan provider install functionality"""

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

    def test_with_dependencies(
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

        # Verify subprocess.run was called with conan install command
        conan_setup_mocks['subprocess_run'].assert_called_once()
        call_args = conan_setup_mocks['subprocess_run'].call_args[0][0]
        assert call_args[0] == 'conan'
        assert call_args[1] == 'install'
        assert '--build' in call_args
        assert 'missing' in call_args
        assert '--profile:host' in call_args
        assert '--profile:build' in call_args
        assert '--output-folder' in call_args

    def test_conan_command_failure(
        self,
        plugin: ConanProvider,
        conan_temp_conanfile: Path,
        conan_mock_dependencies: list[Requirement],
        mocker: MockerFixture,
    ) -> None:
        """Test install method when conan CLI command fails

        Args:
            plugin: The plugin instance
            conan_temp_conanfile: Path to temporary conanfile.py
            conan_mock_dependencies: List of mock dependencies
            mocker: Pytest mocker fixture
        """
        # Mock builder
        mock_builder = mocker.Mock()
        mock_builder.generate_conanfile = mocker.Mock()
        plugin.builder = mock_builder  # type: ignore[attr-defined]

        # Mock resolve_conan_dependency
        def mock_resolve(requirement: Requirement) -> ConanDependency:
            return ConanDependency(name=requirement.name)

        mocker.patch('cppython.plugins.conan.plugin.resolve_conan_dependency', side_effect=mock_resolve)

        # Mock subprocess.run to simulate command failure
        mock_subprocess_run = mocker.patch('cppython.plugins.conan.plugin.subprocess.run')
        mock_subprocess_run.side_effect = subprocess.CalledProcessError(
            1, ['conan', 'install'], stderr='Conan CLI error: package not found'
        )

        # Add a dependency
        plugin.core_data.cppython_data.dependencies = [conan_mock_dependencies[0]]

        # Execute and verify exception is raised
        with pytest.raises(
            ProviderInstallationError,
            match='Failed to install dependencies:.*Conan CLI error: package not found',
        ):
            plugin.install()

        # Verify builder was still called
        mock_builder.generate_conanfile.assert_called_once()

        # Verify subprocess.run was attempted
        mock_subprocess_run.assert_called_once()

    def test_with_update_flag(
        self,
        plugin: ConanProvider,
        conan_temp_conanfile: Path,
        conan_mock_dependencies: list[Requirement],
        conan_setup_mocks: dict[str, Mock],
    ) -> None:
        """Test install method passes update flag to CLI when update=True

        Args:
            plugin: The plugin instance
            conan_temp_conanfile: Path to temporary conanfile.py
            conan_mock_dependencies: List of mock dependencies
            conan_setup_mocks: Dictionary containing all mocks
        """
        # Setup dependencies
        plugin.core_data.cppython_data.dependencies = conan_mock_dependencies

        # Execute update instead of install
        plugin.update()

        # Verify subprocess.run was called with --update flag
        conan_setup_mocks['subprocess_run'].assert_called_once()
        call_args = conan_setup_mocks['subprocess_run'].call_args[0][0]
        assert '--update' in call_args

    def test_with_custom_profiles(
        self,
        plugin: ConanProvider,
        conan_temp_conanfile: Path,
        conan_mock_dependencies: list[Requirement],
        conan_setup_mocks: dict[str, Mock],
        mocker: MockerFixture,
    ) -> None:
        """Test install method uses custom profiles when specified

        Args:
            plugin: The plugin instance
            conan_temp_conanfile: Path to temporary conanfile.py
            conan_mock_dependencies: List of mock dependencies
            conan_setup_mocks: Dictionary containing all mocks
            mocker: Pytest mocker fixture
        """
        # Mock custom profiles
        custom_host_profile = mocker.Mock()
        custom_build_profile = mocker.Mock()
        
        # Override profiles in the plugin data
        plugin.data.host_profile = custom_host_profile
        plugin.data.build_profile = custom_build_profile

        # Setup dependencies
        plugin.core_data.cppython_data.dependencies = conan_mock_dependencies

        # Execute
        plugin.install()

        # Verify subprocess.run was called with custom profiles
        conan_setup_mocks['subprocess_run'].assert_called_once()
        call_args = conan_setup_mocks['subprocess_run'].call_args[0][0]
        
        # Find profile arguments
        profile_host_idx = call_args.index('--profile:host')
        profile_build_idx = call_args.index('--profile:build')
        
        assert call_args[profile_host_idx + 1] == str(custom_host_profile)
        assert call_args[profile_build_idx + 1] == str(custom_build_profile)
