"""Composable test types"""

from abc import ABCMeta, abstractmethod
from importlib.metadata import entry_points
from typing import Any, LiteralString, cast

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
    ProjectConfiguration,
    ProjectData,
)
from cppython.test.pytest.variants import (
    generator_variants,
    provider_variants,
    scm_variants,
)


class BaseTests[T: Plugin](metaclass=ABCMeta):
    """Shared testing information for all plugin test classes."""

    @abstractmethod
    @pytest.fixture(name='plugin_type', scope='session')
    def fixture_plugin_type(self) -> type[T]:
        """A required testing hook that allows type generation"""
        raise NotImplementedError('Override this fixture')

    @staticmethod
    @pytest.fixture(
        name='cppython_plugin_data',
        scope='session',
    )
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
    @pytest.fixture(
        name='core_plugin_data',
        scope='session',
    )
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

    @staticmethod
    @pytest.fixture(name='plugin_group_name', scope='session')
    def fixture_plugin_group_name() -> LiteralString:
        """A required testing hook that allows plugin group name generation

        Returns:
            The plugin group name
        """
        return 'cppython'


class BaseIntegrationTests[T: Plugin](BaseTests[T], metaclass=ABCMeta):
    """Integration testing information for all plugin test classes"""

    @staticmethod
    def test_entry_point(plugin_type: type[T], plugin_group_name: LiteralString) -> None:
        """Verify that the plugin was registered

        Args:
            plugin_type: The type to register
            plugin_group_name: The group name for the plugin type
        """
        # We only require the entry point to be registered if the plugin is not a Mocked type
        if plugin_type.name() == 'mock':
            pytest.skip('Mocked plugin type')

        types = []
        for entry in list(entry_points(group=f'{plugin_group_name}.{plugin_type.group()}')):
            types.append(entry.load())

        assert plugin_type in types

    @staticmethod
    def test_name(plugin_type: type[Plugin]) -> None:
        """Verifies the the class name allows name extraction

        Args:
            plugin_type: The type to register
        """
        assert plugin_type.group()
        assert len(plugin_type.group())

        assert plugin_type.name()
        assert len(plugin_type.name())


class BaseUnitTests[T: Plugin](BaseTests[T], metaclass=ABCMeta):
    """Unit testing information for all plugin test classes"""

    @staticmethod
    def test_feature_extraction(plugin_type: type[T], project_configuration: ProjectConfiguration) -> None:
        """Test the feature extraction of a plugin.

        This method tests the feature extraction functionality of a plugin by asserting that the features
        returned by the plugin are correct for the given project configuration.

        Args:
            plugin_type: The type of plugin to test.
            project_configuration: The project configuration to use for testing.
        """
        assert plugin_type.features(project_configuration.pyproject_file.parent)

    @staticmethod
    def test_information(plugin_type: type[T]) -> None:
        """Test the information method of a plugin.

        This method asserts that the `information` method of the given plugin type returns a value.

        Args:
            plugin_type: The type of the plugin to test.
        """
        assert plugin_type.information()


class PluginTests[T: Plugin](BaseTests[T], metaclass=ABCMeta):
    """Testing information for basic plugin test classes."""

    @staticmethod
    @pytest.fixture(
        name='plugin',
        scope='session',
    )
    def fixture_plugin(
        plugin_type: type[T],
        plugin_group_data: PluginGroupData,
    ) -> T:
        """Overridden plugin generator for creating a populated data plugin type

        Args:
            plugin_type: Plugin type
            plugin_group_data: The data group configuration

        Returns:
            A newly constructed provider
        """
        plugin = plugin_type(plugin_group_data)

        return plugin


class PluginIntegrationTests[T: Plugin](BaseIntegrationTests[T], metaclass=ABCMeta):
    """Integration testing information for basic plugin test classes"""


class PluginUnitTests[T: Plugin](BaseUnitTests[T], metaclass=ABCMeta):
    """Unit testing information for basic plugin test classes"""


class DataPluginTests[T: DataPlugin](BaseTests[T], metaclass=ABCMeta):
    """Shared testing information for all data plugin test classes."""

    @staticmethod
    @pytest.fixture(
        name='plugin',
        scope='session',
    )
    def fixture_plugin(
        plugin_type: type[T],
        plugin_group_data: DataPluginGroupData,
        core_plugin_data: CorePluginData,
        plugin_data: dict[str, Any],
    ) -> T:
        """Overridden plugin generator for creating a populated data plugin type

        Args:
            plugin_type: Plugin type
            plugin_group_data: The data group configuration
            core_plugin_data: The core metadata
            plugin_data: The data table

        Returns:
            A newly constructed provider
        """
        plugin = plugin_type(plugin_group_data, core_plugin_data, plugin_data)

        return plugin


class DataPluginIntegrationTests[T: DataPlugin](BaseIntegrationTests[T], metaclass=ABCMeta):
    """Integration testing information for all data plugin test classes"""


class DataPluginUnitTests[T: DataPlugin](BaseUnitTests[T], metaclass=ABCMeta):
    """Unit testing information for all data plugin test classes"""


class ProviderTests[T: Provider](DataPluginTests[T], metaclass=ABCMeta):
    """Shared functionality between the different Provider testing categories"""

    @staticmethod
    @pytest.fixture(name='plugin_configuration_type', scope='session')
    def fixture_plugin_configuration_type() -> type[ProviderPluginGroupData]:
        """A required testing hook that allows plugin configuration data generation

        Returns:
            The configuration type
        """
        return ProviderPluginGroupData

    @staticmethod
    @pytest.fixture(name='plugin_group_data', scope='session')
    def fixture_plugin_group_data(
        project_data: ProjectData, cppython_plugin_data: CPPythonPluginData
    ) -> ProviderPluginGroupData:
        """Generates plugin configuration data generation from environment configuration

        Args:
            project_data: The project data fixture
            cppython_plugin_data:The plugin configuration fixture

        Returns:
            The plugin configuration
        """
        return resolve_provider(project_data=project_data, cppython_data=cppython_plugin_data)

    @staticmethod
    @pytest.fixture(
        name='provider_type',
        scope='session',
        params=provider_variants,
    )
    def fixture_provider_type(plugin_type: type[T]) -> type[T]:
        """Fixture defining all testable variations mock Providers

        Args:
            plugin_type: Plugin type

        Returns:
            Variation of a Provider
        """
        return plugin_type

    @staticmethod
    @pytest.fixture(
        name='generator_type',
        scope='session',
        params=generator_variants,
    )
    def fixture_generator_type(request: pytest.FixtureRequest) -> type[Generator]:
        """Fixture defining all testable variations mock Generator

        Args:
            request: Parameterization list

        Returns:
            Variation of a Generator
        """
        generator_type = cast(type[Generator], request.param)

        return generator_type

    @staticmethod
    @pytest.fixture(
        name='scm_type',
        scope='session',
        params=scm_variants,
    )
    def fixture_scm_type(request: pytest.FixtureRequest) -> type[SCM]:
        """Fixture defining all testable variations mock Generator

        Args:
            request: Parameterization list

        Returns:
            Variation of a Generator
        """
        scm_type = cast(type[SCM], request.param)

        return scm_type


class GeneratorTests[T: Generator](DataPluginTests[T], metaclass=ABCMeta):
    """Shared functionality between the different Generator testing categories"""

    @staticmethod
    @pytest.fixture(name='plugin_configuration_type', scope='session')
    def fixture_plugin_configuration_type() -> type[GeneratorPluginGroupData]:
        """A required testing hook that allows plugin configuration data generation

        Returns:
            The configuration type
        """
        return GeneratorPluginGroupData

    @staticmethod
    @pytest.fixture(name='plugin_group_data', scope='session')
    def fixture_plugin_group_data(
        project_data: ProjectData, cppython_plugin_data: CPPythonPluginData
    ) -> GeneratorPluginGroupData:
        """Generates plugin configuration data generation from environment configuration

        Args:
            project_data: The project data fixture
            cppython_plugin_data:The plugin configuration fixture

        Returns:
            The plugin configuration
        """
        return resolve_generator(project_data=project_data, cppython_data=cppython_plugin_data)

    @staticmethod
    @pytest.fixture(
        name='provider_type',
        scope='session',
        params=provider_variants,
    )
    def fixture_provider_type(request: pytest.FixtureRequest) -> type[Provider]:
        """Fixture defining all testable variations mock Providers

        Args:
            request: Parameterization list

        Returns:
            Variation of a Provider
        """
        provider_type = cast(type[Provider], request.param)

        return provider_type

    @staticmethod
    @pytest.fixture(
        name='generator_type',
        scope='session',
    )
    def fixture_generator_type(plugin_type: type[T]) -> type[T]:
        """Override

        Args:
            plugin_type: Plugin type

        Returns:
            Plugin type
        """
        return plugin_type

    @staticmethod
    @pytest.fixture(
        name='scm_type',
        scope='session',
        params=scm_variants,
    )
    def fixture_scm_type(request: pytest.FixtureRequest) -> type[SCM]:
        """Fixture defining all testable variations mock Generator

        Args:
            request: Parameterization list

        Returns:
            Variation of a Generator
        """
        scm_type = cast(type[SCM], request.param)

        return scm_type


class SCMTests[T: SCM](PluginTests[T], metaclass=ABCMeta):
    """Shared functionality between the different SCM testing categories"""

    @staticmethod
    @pytest.fixture(name='plugin_configuration_type', scope='session')
    def fixture_plugin_configuration_type() -> type[SCMPluginGroupData]:
        """A required testing hook that allows plugin configuration data generation

        Returns:
            The configuration type
        """
        return SCMPluginGroupData

    @staticmethod
    @pytest.fixture(name='plugin_group_data', scope='session')
    def fixture_plugin_group_data(
        project_data: ProjectData, cppython_plugin_data: CPPythonPluginData
    ) -> SCMPluginGroupData:
        """Generates plugin configuration data generation from environment configuration

        Args:
            project_data: The project data fixture
            cppython_plugin_data:The plugin configuration fixture

        Returns:
            The plugin configuration
        """
        return resolve_scm(project_data=project_data, cppython_data=cppython_plugin_data)

    @staticmethod
    @pytest.fixture(
        name='provider_type',
        scope='session',
        params=provider_variants,
    )
    def fixture_provider_type(request: pytest.FixtureRequest) -> type[Provider]:
        """Fixture defining all testable variations mock Providers

        Args:
            request: Parameterization list

        Returns:
            Variation of a Provider
        """
        provider_type = cast(type[Provider], request.param)

        return provider_type

    @staticmethod
    @pytest.fixture(
        name='generator_type',
        scope='session',
        params=generator_variants,
    )
    def fixture_generator_type(request: pytest.FixtureRequest) -> type[Generator]:
        """Fixture defining all testable variations mock Generator

        Args:
            request: Parameterization list

        Returns:
            Variation of a Generator
        """
        generator_type = cast(type[Generator], request.param)

        return generator_type

    @staticmethod
    @pytest.fixture(
        name='scm_type',
        scope='session',
        params=scm_variants,
    )
    def fixture_scm_type(plugin_type: type[T]) -> type[SCM]:
        """Fixture defining all testable variations mock Generator

        Args:
            plugin_type: Parameterization list

        Returns:
            Variation of a Generator
        """
        return plugin_type
