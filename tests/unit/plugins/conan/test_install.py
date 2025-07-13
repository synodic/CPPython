"""Unit tests for the conan plugin install functionality"""

from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest
from packaging.requirements import Requirement
from pytest_mock import MockerFixture

from cppython.plugins.conan.plugin import ConanProvider
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
        mocker: MockerFixture,
        plugin: ConanProvider,
        conan_temp_conanfile: Path,
        conan_mock_dependencies: list[Requirement],
        conan_setup_mocks: dict[str, Mock],
    ) -> None:
        """Test install method with dependencies and existing conanfile

        Args:
            mocker: Pytest mocker fixture
            plugin: The plugin instance
            conan_temp_conanfile: Path to temporary conanfile.py
            conan_mock_dependencies: List of mock dependencies
            conan_setup_mocks: Dictionary containing all mocks
        """
        # Setup subprocess mock to return success
        mock_subprocess = mocker.patch('cppython.plugins.conan.plugin.subprocess.run')
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = 'Install completed successfully'
        mock_subprocess.return_value.stderr = ''

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

        # Verify subprocess was called with correct command
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args
        cmd = call_args[0][0]

        # Check command structure
        assert cmd[0] == 'conan'
        assert cmd[1] == 'install'
        assert cmd[2] == str(conan_temp_conanfile)
        assert '--output-folder' in cmd
        assert '--build' in cmd
        assert 'missing' in cmd
        assert '--update' not in cmd  # install mode, not update

        # Check working directory
        assert call_args[1]['cwd'] == str(plugin.core_data.project_data.project_root)

    def test_install_conan_command_failure(
        self,
        mocker: MockerFixture,
        plugin: ConanProvider,
        conan_temp_conanfile: Path,
        conan_mock_dependencies: list[Requirement],
        conan_setup_mocks: dict[str, Mock],
    ) -> None:
        """Test install method when conan command fails

        Args:
            mocker: Pytest mocker fixture
            plugin: The plugin instance
            conan_temp_conanfile: Path to temporary conanfile.py
            conan_mock_dependencies: List of mock dependencies
            conan_setup_mocks: Dictionary containing all mocks
        """
        # Make subprocess return failure
        mock_subprocess = mocker.patch('cppython.plugins.conan.plugin.subprocess.run')
        mock_subprocess.return_value.returncode = 1
        mock_subprocess.return_value.stdout = ''
        mock_subprocess.return_value.stderr = 'Conan install failed: package not found'

        # Add a dependency
        plugin.core_data.cppython_data.dependencies = [conan_mock_dependencies[0]]

        # Execute and verify exception is raised
        with pytest.raises(ProviderInstallationError, match='Conan install failed with return code 1'):
            plugin.install()

        # Verify builder was still called
        conan_setup_mocks['builder'].generate_conanfile.assert_called_once()

        # Verify subprocess was called
        mock_subprocess.assert_called_once()
