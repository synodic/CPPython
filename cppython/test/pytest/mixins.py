"""Core test mixins and utilities that can be used by any test class.

This module provides the foundational testing infrastructure that all test classes
can inherit from or use directly. These are meant to be mixed into test classes
as needed, not inherited in a strict hierarchy.
"""

from abc import ABCMeta, abstractmethod
from typing import Any, LiteralString

import pytest

from cppython.core.resolution import resolve_cppython_plugin
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


class TestMixin[T: Plugin](metaclass=ABCMeta):
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


class PluginTestMixin[T: Plugin](TestMixin[T], metaclass=ABCMeta):
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


class DataPluginTestMixin[T: DataPlugin](TestMixin[T], metaclass=ABCMeta):
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
