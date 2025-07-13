"""Core test mixins and utilities that can be used by any test class.

This module provides the foundational testing infrastructure that all test classes
can inherit from or use directly. These are meant to be mixed into test classes
as needed, not inherited in a strict hierarchy.
"""

from abc import ABC, abstractmethod
from typing import Any, LiteralString

import pytest

from cppython.core.plugin_schema.generator import Generator, GeneratorPluginGroupData
from cppython.core.plugin_schema.provider import Provider, ProviderPluginGroupData
from cppython.core.plugin_schema.scm import SCM, SCMPluginGroupData
from cppython.core.resolution import (
    resolve_cppython_plugin,
    resolve_generator,
    resolve_provider,
    resolve_scm,
)
from cppython.core.schema import (
    CorePluginData,
    CPPythonData,
    CPPythonPluginData,
    DataPlugin,
    DataPluginGroupData,
    PEP621Data,
    Plugin,
    PluginGroupData,
    ProjectData,
)
from cppython.test.data.mocks import generator_variants, provider_variants, scm_variants


class TestMixin[T: Plugin](ABC):
    """Core mixin that provides basic plugin construction capabilities.

    Any test class can inherit from this to get access to standard plugin
    construction fixtures. This is the base layer that provides the minimal
    infrastructure needed for plugin testing.
    """

    @abstractmethod
    @pytest.fixture(name='plugin_type', scope='session')
    def fixture_plugin_type(self) -> type[T]:
        """A required testing hook that allows type generation

        This must be implemented by any concrete test class to specify
        which plugin type is being tested.
        """
        raise NotImplementedError('Override this fixture')

    @abstractmethod
    @pytest.fixture(name='plugin_data', scope='session')
    def fixture_plugin_data(self) -> dict[str, Any]:
        """A required testing hook that allows plugin configuration data generation

        This must be implemented by any concrete test class to provide
        the configuration data for the plugin being tested.
        """
        raise NotImplementedError('Override this fixture')

    @staticmethod
    @pytest.fixture(name='plugin_group_name', scope='session')
    def fixture_plugin_group_name() -> LiteralString:
        """A required testing hook that allows plugin group name generation

        Returns:
            The plugin group name
        """
        return 'cppython'

    @staticmethod
    @pytest.fixture(name='cppython_plugin_data')
    def fixture_cppython_plugin_data(cppython_data: CPPythonData, plugin_type: type[T]) -> CPPythonPluginData:
        """Fixture for created the plugin CPPython table

        Args:
            cppython_data: The CPPython table to help the resolve
            plugin_type: The data plugin type

        Returns:
            The plugin specific CPPython table information
        """
        return resolve_cppython_plugin(cppython_data, plugin_type)

    @staticmethod
    @pytest.fixture(name='core_plugin_data')
    def fixture_core_plugin_data(
        cppython_plugin_data: CPPythonPluginData, project_data: ProjectData, pep621_data: PEP621Data
    ) -> CorePluginData:
        """Fixture for creating the wrapper CoreData type

        Args:
            cppython_plugin_data: CPPython data
            project_data: The project data
            pep621_data: Project table data

        Returns:
            Wrapper Core Type
        """
        return CorePluginData(cppython_data=cppython_plugin_data, project_data=project_data, pep621_data=pep621_data)


class PluginTestMixin[T: Plugin](TestMixin[T], ABC):
    """Plugin construction mixin for simple plugins.

    Provides plugin instance creation for plugins that don't need complex
    configuration data (like SCM plugins).
    """

    @staticmethod
    @pytest.fixture(name='plugin')
    def fixture_plugin(plugin_type: type[T], plugin_group_data: PluginGroupData) -> T:
        """Create a basic plugin instance

        Args:
            plugin_type: Plugin type
            plugin_group_data: The data group configuration

        Returns:
            A newly constructed plugin
        """
        return plugin_type(plugin_group_data)


class DataPluginTestMixin[T: DataPlugin](TestMixin[T], ABC):
    """Data plugin construction mixin for complex plugins.

    Provides plugin instance creation for plugins that need rich configuration
    data (like Provider and Generator plugins).
    """

    @staticmethod
    @pytest.fixture(name='plugin')
    def fixture_plugin(
        plugin_type: type[T],
        plugin_group_data: DataPluginGroupData,
        core_plugin_data: CorePluginData,
        plugin_data: dict[str, Any],
    ) -> T:
        """Create a data plugin instance

        Args:
            plugin_type: Plugin type
            plugin_group_data: The data group configuration
            core_plugin_data: The core metadata
            plugin_data: The data table

        Returns:
            A newly constructed provider
        """
        return plugin_type(plugin_group_data, core_plugin_data, plugin_data)


class ProviderPluginTestMixin[T: Provider](DataPluginTestMixin[T], ABC):
    """Data plugin construction mixin specifically for Provider plugins.

    Provides all necessary fixtures for Provider plugin testing, including
    the plugin_group_data fixture that creates ProviderPluginGroupData.
    """

    @staticmethod
    @pytest.fixture(name='plugin_group_data')
    def fixture_plugin_group_data(
        project_data: ProjectData, cppython_plugin_data: CPPythonPluginData
    ) -> ProviderPluginGroupData:
        """Generate Provider plugin configuration data

        Args:
            project_data: The project data
            cppython_plugin_data: CPPython plugin data

        Returns:
            Provider plugin group data
        """
        return resolve_provider(project_data=project_data, cppython_data=cppython_plugin_data)

    # Cross-plugin testing fixtures for ensuring compatibility
    @staticmethod
    @pytest.fixture(name='provider_type', scope='session')
    def fixture_provider_type(plugin_type: type[T]) -> type[T]:
        """Return this provider type for cross-plugin testing

        Args:
            plugin_type: The provider plugin type being tested

        Returns:
            The same provider type
        """
        return plugin_type

    @staticmethod
    @pytest.fixture(name='generator_type', scope='session')
    def fixture_generator_type(request: 'pytest.FixtureRequest') -> type[Generator]:
        """Provide generator variants for cross-plugin testing

        Args:
            request: Pytest fixture request

        Returns:
            Generator type for testing
        """
        # Use the first generator variant for testing
        return generator_variants[0]

    @staticmethod
    @pytest.fixture(name='scm_type', scope='session')
    def fixture_scm_type(request: 'pytest.FixtureRequest') -> type[SCM]:
        """Provide SCM variants for cross-plugin testing

        Args:
            request: Pytest fixture request

        Returns:
            SCM type for testing
        """
        # Use the first SCM variant for testing
        return scm_variants[0]

    @staticmethod
    @pytest.fixture(name='plugin_configuration_type', scope='session')
    def fixture_plugin_configuration_type() -> type[ProviderPluginGroupData]:
        """Required hook for Provider plugin configuration data generation"""
        return ProviderPluginGroupData


class GeneratorPluginTestMixin[T: Generator](DataPluginTestMixin[T], ABC):
    """Data plugin construction mixin specifically for Generator plugins.

    Provides all necessary fixtures for Generator plugin testing, including
    the plugin_group_data fixture that creates GeneratorPluginGroupData.
    """

    @staticmethod
    @pytest.fixture(name='plugin_group_data')
    def fixture_plugin_group_data(
        project_data: ProjectData, cppython_plugin_data: CPPythonPluginData
    ) -> GeneratorPluginGroupData:
        """Generate Generator plugin configuration data

        Args:
            project_data: The project data
            cppython_plugin_data: CPPython plugin data

        Returns:
            Generator plugin group data
        """
        return resolve_generator(project_data=project_data, cppython_data=cppython_plugin_data)

    # Cross-plugin testing fixtures for ensuring compatibility
    @staticmethod
    @pytest.fixture(name='provider_type', scope='session')
    def fixture_provider_type(request: 'pytest.FixtureRequest') -> type[Provider]:
        """Provide provider variants for cross-plugin testing

        Args:
            request: Pytest fixture request

        Returns:
            Provider type for testing
        """
        # Use the first provider variant for testing
        return provider_variants[0]

    @staticmethod
    @pytest.fixture(name='generator_type', scope='session')
    def fixture_generator_type(plugin_type: type[T]) -> type[T]:
        """Return this generator type for cross-plugin testing

        Args:
            plugin_type: The generator plugin type being tested

        Returns:
            The same generator type
        """
        return plugin_type

    @staticmethod
    @pytest.fixture(name='scm_type', scope='session')
    def fixture_scm_type(request: 'pytest.FixtureRequest') -> type[SCM]:
        """Provide SCM variants for cross-plugin testing

        Args:
            request: Pytest fixture request

        Returns:
            SCM type for testing
        """
        # Use the first SCM variant for testing
        return scm_variants[0]

    @staticmethod
    @pytest.fixture(name='plugin_configuration_type', scope='session')
    def fixture_plugin_configuration_type() -> type[GeneratorPluginGroupData]:
        """Required hook for Generator plugin configuration data generation"""
        return GeneratorPluginGroupData


class SCMPluginTestMixin[T: SCM](PluginTestMixin[T], ABC):
    """Plugin construction mixin specifically for SCM plugins.

    Provides all necessary fixtures for SCM plugin testing, including
    the plugin_group_data fixture that creates SCMPluginGroupData.
    """

    @staticmethod
    @pytest.fixture(name='plugin_group_data')
    def fixture_plugin_group_data(
        project_data: ProjectData, cppython_plugin_data: CPPythonPluginData
    ) -> SCMPluginGroupData:
        """Generate SCM plugin configuration data

        Args:
            project_data: The project data
            cppython_plugin_data: CPPython plugin data

        Returns:
            SCM plugin group data
        """
        return resolve_scm(project_data=project_data, cppython_data=cppython_plugin_data)

    # Cross-plugin testing fixtures for ensuring compatibility
    @staticmethod
    @pytest.fixture(name='provider_type', scope='session')
    def fixture_provider_type(request: 'pytest.FixtureRequest') -> type[Provider]:
        """Provide provider variants for cross-plugin testing

        Args:
            request: Pytest fixture request

        Returns:
            Provider type for testing
        """
        # Use the first provider variant for testing
        return provider_variants[0]

    @staticmethod
    @pytest.fixture(name='generator_type', scope='session')
    def fixture_generator_type(request: 'pytest.FixtureRequest') -> type[Generator]:
        """Provide generator variants for cross-plugin testing

        Args:
            request: Pytest fixture request

        Returns:
            Generator type for testing
        """
        # Use the first generator variant for testing
        return generator_variants[0]

    @staticmethod
    @pytest.fixture(name='scm_type', scope='session')
    def fixture_scm_type(plugin_type: type[T]) -> type[T]:
        """Return this SCM type for cross-plugin testing

        Args:
            plugin_type: The SCM plugin type being tested

        Returns:
            The same SCM type
        """
        return plugin_type

    @staticmethod
    @pytest.fixture(name='plugin_configuration_type', scope='session')
    def fixture_plugin_configuration_type() -> type[SCMPluginGroupData]:
        """Required hook for SCM plugin configuration data generation"""
        return SCMPluginGroupData
