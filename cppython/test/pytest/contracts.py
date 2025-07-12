"""Plugin test contracts that define standard test requirements.

This module contains abstract base classes that define the testing contracts
for each plugin type. Each plugin implementation should inherit from the
appropriate contract class exactly once to ensure they fulfill the required
testing obligations.

These contracts combine the core fixtures with plugin-type-specific requirements.
"""

import asyncio
from abc import ABCMeta
from importlib.metadata import entry_points
from pathlib import Path
from typing import Any, LiteralString

import pytest

from cppython.core.plugin_schema.generator import Generator, GeneratorPluginGroupData
from cppython.core.plugin_schema.provider import Provider, ProviderPluginGroupData
from cppython.core.plugin_schema.scm import SCM, SCMPluginGroupData
from cppython.core.resolution import resolve_generator, resolve_provider, resolve_scm
from cppython.core.schema import (
    CorePluginData,
    CPPythonPluginData,
    DataPluginGroupData,
    Plugin,
    ProjectConfiguration,
    ProjectData,
)
from cppython.test.data.mocks import generator_variants, provider_variants, scm_variants
from cppython.test.pytest.mixins import (
    DataPluginTestMixin,
    PluginTestMixin,
)
from cppython.utility.utility import canonicalize_type


class PluginTestValidation:
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


class DataPluginTestValidation(PluginTestValidation):
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


class ProviderTestContract[T: Provider](DataPluginTestMixin[T], DataPluginTestValidation, metaclass=ABCMeta):
    """Test contract for Provider plugins.

    Each Provider plugin should have exactly one test class that inherits from this
    to ensure it fulfills all Provider testing requirements.
    """

    @staticmethod
    @pytest.fixture(name='plugin_configuration_type', scope='session')
    def fixture_plugin_configuration_type() -> type[ProviderPluginGroupData]:
        """Required hook for Provider plugin configuration data generation"""
        return ProviderPluginGroupData

    @staticmethod
    @pytest.fixture(name='plugin_group_data')
    def fixture_plugin_group_data(
        project_data: ProjectData, cppython_plugin_data: CPPythonPluginData
    ) -> ProviderPluginGroupData:
        """Generate Provider plugin configuration data"""
        return resolve_provider(project_data=project_data, cppython_data=cppython_plugin_data)

    # Cross-plugin testing fixtures for ensuring compatibility
    @staticmethod
    @pytest.fixture(name='provider_type', scope='session', params=provider_variants)
    def fixture_provider_type(plugin_type: type[T]) -> type[T]:
        """Return this provider type for cross-plugin testing"""
        return plugin_type

    @staticmethod
    @pytest.fixture(name='generator_type', scope='session', params=generator_variants)
    def fixture_generator_type(request: pytest.FixtureRequest) -> type[Generator]:
        """Provide generator variants for cross-plugin testing"""
        return request.param

    @staticmethod
    @pytest.fixture(name='scm_type', scope='session', params=scm_variants)
    def fixture_scm_type(request: pytest.FixtureRequest) -> type[SCM]:
        """Provide SCM variants for cross-plugin testing"""
        return request.param


class ProviderIntegrationTestContract[T: Provider](ProviderTestContract[T], metaclass=ABCMeta):
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


class GeneratorTestContract[T: Generator](DataPluginTestMixin[T], DataPluginTestValidation, metaclass=ABCMeta):
    """Test contract for Generator plugins.

    Each Generator plugin should have exactly one test class that inherits from this
    to ensure it fulfills all Generator testing requirements.
    """

    @staticmethod
    @pytest.fixture(name='plugin_configuration_type', scope='session')
    def fixture_plugin_configuration_type() -> type[GeneratorPluginGroupData]:
        """Required hook for Generator plugin configuration data generation"""
        return GeneratorPluginGroupData

    @staticmethod
    @pytest.fixture(name='plugin_group_data')
    def fixture_plugin_group_data(
        project_data: ProjectData, cppython_plugin_data: CPPythonPluginData
    ) -> GeneratorPluginGroupData:
        """Generate Generator plugin configuration data"""
        return resolve_generator(project_data=project_data, cppython_data=cppython_plugin_data)

    # Cross-plugin testing fixtures for ensuring compatibility
    @staticmethod
    @pytest.fixture(name='provider_type', scope='session', params=provider_variants)
    def fixture_provider_type(request: pytest.FixtureRequest) -> type[Provider]:
        """Provide provider variants for cross-plugin testing"""
        return request.param

    @staticmethod
    @pytest.fixture(name='generator_type', scope='session')
    def fixture_generator_type(plugin_type: type[T]) -> type[T]:
        """Return this generator type for cross-plugin testing"""
        return plugin_type

    @staticmethod
    @pytest.fixture(name='scm_type', scope='session', params=scm_variants)
    def fixture_scm_type(request: pytest.FixtureRequest) -> type[SCM]:
        """Provide SCM variants for cross-plugin testing"""
        return request.param


class GeneratorIntegrationTestContract[T: Generator](GeneratorTestContract[T], metaclass=ABCMeta):
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


class SCMTestContract[T: SCM](PluginTestMixin[T], PluginTestValidation, metaclass=ABCMeta):
    """Test contract for SCM plugins.

    Each SCM plugin should have exactly one test class that inherits from this
    to ensure it fulfills all SCM testing requirements.
    """

    @staticmethod
    @pytest.fixture(name='plugin_configuration_type', scope='session')
    def fixture_plugin_configuration_type() -> type[SCMPluginGroupData]:
        """Required hook for SCM plugin configuration data generation"""
        return SCMPluginGroupData

    @staticmethod
    @pytest.fixture(name='plugin_group_data')
    def fixture_plugin_group_data(
        project_data: ProjectData, cppython_plugin_data: CPPythonPluginData
    ) -> SCMPluginGroupData:
        """Generate SCM plugin configuration data"""
        return resolve_scm(project_data=project_data, cppython_data=cppython_plugin_data)

    # Cross-plugin testing fixtures for ensuring compatibility
    @staticmethod
    @pytest.fixture(name='provider_type', scope='session', params=provider_variants)
    def fixture_provider_type(request: pytest.FixtureRequest) -> type[Provider]:
        """Provide provider variants for cross-plugin testing"""
        return request.param

    @staticmethod
    @pytest.fixture(name='generator_type', scope='session', params=generator_variants)
    def fixture_generator_type(request: pytest.FixtureRequest) -> type[Generator]:
        """Provide generator variants for cross-plugin testing"""
        return request.param

    @staticmethod
    @pytest.fixture(name='scm_type', scope='session', params=scm_variants)
    def fixture_scm_type(plugin_type: type[T]) -> type[T]:
        """Return this SCM type for cross-plugin testing"""
        return plugin_type


class SCMIntegrationTestContract[T: SCM](SCMTestContract[T], metaclass=ABCMeta):
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
