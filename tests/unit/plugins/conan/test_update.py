"""Unit tests for the conan plugin update functionality

This module tests the update-specific behavior and differences from install.
The core installation functionality is tested in test_install.py since both
install() and update() now share the same underlying implementation.
"""

from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest
from packaging.requirements import Requirement

from cppython.plugins.conan.plugin import ConanProvider
from cppython.test.pytest.mixins import ProviderPluginTestMixin

pytest_plugins = ['tests.fixtures.conan']


class TestConanUpdate(ProviderPluginTestMixin[ConanProvider]):
    """Tests for the Conan provider update-specific functionality"""

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

    def test_update_includes_update_flag(
        self,
        plugin: ConanProvider,
        conan_temp_conanfile: Path,
        conan_mock_dependencies: list[Requirement],
        conan_setup_mocks: dict[str, Mock],
    ) -> None:
        """Test that update() method includes --update flag in conan command

        Args:
            plugin: The plugin instance
            conan_temp_conanfile: Path to temporary conanfile.py
            conan_mock_dependencies: List of mock dependencies
            conan_setup_mocks: Dictionary containing all mocks
        """
        # Setup dependencies
        plugin.core_data.cppython_data.dependencies = conan_mock_dependencies

        # Execute update
        plugin.update()

        # Verify subprocess.run was called with --update flag
        conan_setup_mocks['subprocess_run'].assert_called_once()
        call_args = conan_setup_mocks['subprocess_run'].call_args[0][0]
        assert '--update' in call_args

    def test_install_does_not_include_update_flag(
        self,
        plugin: ConanProvider,
        conan_temp_conanfile: Path,
        conan_mock_dependencies: list[Requirement],
        conan_setup_mocks: dict[str, Mock],
    ) -> None:
        """Test that install() method does not include --update flag in conan command

        Args:
            plugin: The plugin instance
            conan_temp_conanfile: Path to temporary conanfile.py
            conan_mock_dependencies: List of mock dependencies
            conan_setup_mocks: Dictionary containing all mocks
        """
        # Setup dependencies
        plugin.core_data.cppython_data.dependencies = conan_mock_dependencies

        # Execute install
        plugin.install()

        # Verify subprocess.run was called without --update flag
        conan_setup_mocks['subprocess_run'].assert_called_once()
        call_args = conan_setup_mocks['subprocess_run'].call_args[0][0]
        assert '--update' not in call_args
