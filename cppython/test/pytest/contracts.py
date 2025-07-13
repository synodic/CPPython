"""Plugin test contracts that define standard test requirements.

This module contains abstract base classes that define the testing contracts
for each plugin type. Each plugin implementation should inherit from the
appropriate contract class exactly once to ensure they fulfill the required
testing obligations.

These contracts combine the core fixtures with plugin-type-specific requirements.
"""

import asyncio
from abc import ABC
from importlib.metadata import entry_points
from pathlib import Path
from typing import Any, LiteralString

import pytest

from cppython.core.plugin_schema.generator import Generator
from cppython.core.plugin_schema.provider import Provider
from cppython.core.plugin_schema.scm import SCM
from cppython.core.schema import (
    CorePluginData,
    DataPluginGroupData,
    Plugin,
    ProjectConfiguration,
)
from cppython.test.pytest.mixins import (
    GeneratorPluginTestMixin,
    ProviderPluginTestMixin,
    SCMPluginTestMixin,
)
from cppython.utility.utility import canonicalize_type


class _PluginValidation:
    """Common validation tests that can be applied to any plugin.

    These are generic tests that validate basic plugin behavior regardless
    of the specific plugin type. Test classes can inherit this to get
    standard validation tests.
    """

    @staticmethod
    def test_feature_extraction(plugin_type: type[Plugin], project_configuration: ProjectConfiguration) -> None:
        """Test the feature extraction of a plugin.

        Args:
            plugin_type: The type of plugin to test.
            project_configuration: The project configuration to use for testing.
        """
        assert plugin_type.features(project_configuration.project_root)

    @staticmethod
    def test_information(plugin_type: type[Plugin]) -> None:
        """Test the information method of a plugin.

        Args:
            plugin_type: The type of the plugin to test.
        """
        assert plugin_type.information()

    @staticmethod
    def test_plugin_name_extraction(plugin_type: type[Plugin]) -> None:
        """Verifies the class name allows name extraction

        Args:
            plugin_type: The type to register
        """
        assert plugin_type.group()
        assert len(plugin_type.group())
        assert plugin_type.name()
        assert len(plugin_type.name())


class _DataPluginValidation(_PluginValidation):
    """Validation tests specific to data plugins.

    These tests validate that data plugins can handle various configuration
    scenarios properly.
    """

    @staticmethod
    def test_empty_data_construction(
        plugin_type: type[Any],
        plugin_group_data: DataPluginGroupData,
        core_plugin_data: CorePluginData,
    ) -> None:
        """All data plugins should be able to be constructed with empty data

        Args:
            plugin_type: The plugin type to test
            plugin_group_data: Plugin group configuration
            core_plugin_data: Core plugin data
        """
        plugin = plugin_type(plugin_group_data, core_plugin_data, {})
        assert plugin, 'The plugin should be able to be constructed with empty data'


class ProviderUnitTestContract[T: Provider](ProviderPluginTestMixin[T], _DataPluginValidation, ABC):
    """Test contract for Provider plugins.

    Each Provider plugin should have exactly one test class that inherits from this
    to ensure it fulfills all Provider testing requirements.
    """


class ProviderIntegrationTestContract[T: Provider](ProviderPluginTestMixin[T], ABC):
    """Integration test contract for Provider plugins.

    Providers that need integration testing should inherit from this contract.
    This includes tests that require actual tool installation and execution.
    """

    @staticmethod
    @pytest.fixture(autouse=True, scope='session')
    def _fixture_install_dependency(plugin_type: type[T], install_path: Path) -> None:
        """Forces the provider tool download to only happen once per test session"""
        path = install_path / canonicalize_type(plugin_type).name
        path.mkdir(parents=True, exist_ok=True)
        asyncio.run(plugin_type.download_tooling(path))

    @staticmethod
    def test_entry_point_registration(plugin_type: type[T], plugin_group_name: LiteralString) -> None:
        """Verify that the provider plugin was registered with entry points"""
        if plugin_type.name() == 'mock':
            pytest.skip('Mocked plugin type')

        registered_types = []
        for entry in list(entry_points(group=f'{plugin_group_name}.{plugin_type.group()}')):
            registered_types.append(entry.load())

        assert plugin_type in registered_types

    @staticmethod
    def test_install(plugin: T) -> None:
        """Ensure that the provider install command functions"""
        plugin.install()

    @staticmethod
    def test_update(plugin: T) -> None:
        """Ensure that the provider update command functions"""
        plugin.update()

    @staticmethod
    def test_group_name(plugin_type: type[T]) -> None:
        """Verify that the provider group name is correct"""
        assert canonicalize_type(plugin_type).group == 'provider'


class GeneratorUnitTestContract[T: Generator](GeneratorPluginTestMixin[T], _DataPluginValidation, ABC):
    """Test contract for Generator plugins.

    Each Generator plugin should have exactly one test class that inherits from this
    to ensure it fulfills all Generator testing requirements.
    """


class GeneratorIntegrationTestContract[T: Generator](GeneratorPluginTestMixin[T], ABC):
    """Integration test contract for Generator plugins.

    Generators that need integration testing should inherit from this contract.
    """

    @staticmethod
    def test_entry_point_registration(plugin_type: type[T], plugin_group_name: LiteralString) -> None:
        """Verify that the generator plugin was registered with entry points"""
        if plugin_type.name() == 'mock':
            pytest.skip('Mocked plugin type')

        registered_types = []
        for entry in list(entry_points(group=f'{plugin_group_name}.{plugin_type.group()}')):
            registered_types.append(entry.load())

        assert plugin_type in registered_types

    @staticmethod
    def test_group_name(plugin_type: type[T]) -> None:
        """Verify that the generator group name is correct"""
        assert canonicalize_type(plugin_type).group == 'generator'


class SCMUnitTestContract[T: SCM](SCMPluginTestMixin[T], _PluginValidation, ABC):
    """Test contract for SCM plugins.

    Each SCM plugin should have exactly one test class that inherits from this
    to ensure it fulfills all SCM testing requirements.
    """


class SCMIntegrationTestContract[T: SCM](SCMPluginTestMixin[T], ABC):
    """Integration test contract for SCM plugins.

    SCM plugins that need integration testing should inherit from this contract.
    """

    @staticmethod
    def test_entry_point_registration(plugin_type: type[T], plugin_group_name: LiteralString) -> None:
        """Verify that the SCM plugin was registered with entry points"""
        if plugin_type.name() == 'mock':
            pytest.skip('Mocked plugin type')

        registered_types = []
        for entry in list(entry_points(group=f'{plugin_group_name}.{plugin_type.group()}')):
            registered_types.append(entry.load())

        assert plugin_type in registered_types

    @staticmethod
    def test_group_name(plugin_type: type[T]) -> None:
        """Verify that the SCM group name is correct"""
        assert canonicalize_type(plugin_type).group == 'scm'
