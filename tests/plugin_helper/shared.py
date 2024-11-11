"""Composable test types"""

from abc import ABCMeta
from pathlib import Path
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
from tests.plugin_helper.plugin import BaseTests as SynodicBaseTests
from tests.plugin_helper.plugin import IntegrationTests as SynodicBaseIntegrationTests
from tests.plugin_helper.plugin import UnitTests as SynodicBaseUnitTests
from tests.plugin_helper.variants import (
    generator_variants,
    provider_variants,
    scm_variants,
)


class BaseTests[T: Plugin](SynodicBaseTests[T], metaclass=ABCMeta):
    """Shared testing information for all plugin test classes."""

    @pytest.fixture(name="plugin_type", scope="session")
    def fixture_plugin_type(self) -> type[T]:
        """A required testing hook that allows type generation"""

        raise NotImplementedError("Override this fixture")

    @pytest.fixture(
        name="cppython_plugin_data",
        scope="session",
    )
    def fixture_cppython_plugin_data(self, cppython_data: CPPythonData, plugin_type: type[T]) -> CPPythonPluginData:
        """Fixture for created the plugin CPPython table

        Args:
            cppython_data: The CPPython table to help the resolve
            plugin_type: The data plugin type

        Returns:
            The plugin specific CPPython table information
        """

        return resolve_cppython_plugin(cppython_data, plugin_type)

    @pytest.fixture(
        name="core_plugin_data",
        scope="session",
    )
    def fixture_core_plugin_data(
        self, cppython_plugin_data: CPPythonPluginData, project_data: ProjectData, pep621_data: PEP621Data
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

    @pytest.fixture(name="plugin_group_name", scope="session")
    def fixture_plugin_group_name(self) -> LiteralString:
        """A required testing hook that allows plugin group name generation

        Returns:
            The plugin group name
        """

        return "cppython"


class BaseIntegrationTests[T: Plugin](SynodicBaseIntegrationTests[T], metaclass=ABCMeta):
    """Integration testing information for all plugin test classes"""


class BaseUnitTests[T: Plugin](SynodicBaseUnitTests[T], metaclass=ABCMeta):
    """Unit testing information for all plugin test classes"""

    def test_feature_extraction(self, plugin_type: type[T], project_configuration: ProjectConfiguration) -> None:
        """Test the feature extraction of a plugin.

        This method tests the feature extraction functionality of a plugin by asserting that the features
        returned by the plugin are correct for the given project configuration.

        Args:
            plugin_type: The type of plugin to test.
            project_configuration: The project configuration to use for testing.
        """
        assert plugin_type.features(project_configuration.pyproject_file.parent)

    def test_information(self, plugin_type: type[T]) -> None:
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
        name="plugin",
        scope="session",
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
    """Shared testing information for all data plugin test classes.
    Not inheriting PluginTests to reduce ancestor count
    """

    @staticmethod
    @pytest.fixture(
        name="plugin",
        scope="session",
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

    def test_pyproject_undefined(self, plugin_data_path: Path | None) -> None:
        """Verifies that the directory data provided by plugins does not contain a pyproject.toml file

        Args:
            plugin_data_path: The plugin's tests/data directory
        """

        if plugin_data_path is not None:
            paths = list(plugin_data_path.rglob("pyproject.toml"))

            assert not paths


class ProviderTests[T: Provider](DataPluginTests[T], metaclass=ABCMeta):
    """Shared functionality between the different Provider testing categories"""

    @pytest.fixture(name="plugin_configuration_type", scope="session")
    def fixture_plugin_configuration_type(self) -> type[ProviderPluginGroupData]:
        """A required testing hook that allows plugin configuration data generation

        Returns:
            The configuration type
        """

        return ProviderPluginGroupData

    @pytest.fixture(name="plugin_group_data", scope="session")
    def fixture_plugin_group_data(
        self, project_data: ProjectData, cppython_plugin_data: CPPythonPluginData
    ) -> ProviderPluginGroupData:
        """Generates plugin configuration data generation from environment configuration

        Args:
            project_data: The project data fixture
            cppython_plugin_data:The plugin configuration fixture

        Returns:
            The plugin configuration
        """

        return resolve_provider(project_data=project_data, cppython_data=cppython_plugin_data)

    @pytest.fixture(
        name="provider_type",
        scope="session",
        params=provider_variants,
    )
    def fixture_provider_type(self, plugin_type: type[T]) -> type[T]:
        """Fixture defining all testable variations mock Providers

        Args:
            plugin_type: Plugin type

        Returns:
            Variation of a Provider
        """
        return plugin_type

    @pytest.fixture(
        name="generator_type",
        scope="session",
        params=generator_variants,
    )
    def fixture_generator_type(self, request: pytest.FixtureRequest) -> type[Generator]:
        """Fixture defining all testable variations mock Generator

        Args:
            request: Parameterization list

        Returns:
            Variation of a Generator
        """
        generator_type = cast(type[Generator], request.param)

        return generator_type

    @pytest.fixture(
        name="scm_type",
        scope="session",
        params=scm_variants,
    )
    def fixture_scm_type(self, request: pytest.FixtureRequest) -> type[SCM]:
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

    @pytest.fixture(name="plugin_configuration_type", scope="session")
    def fixture_plugin_configuration_type(self) -> type[GeneratorPluginGroupData]:
        """A required testing hook that allows plugin configuration data generation

        Returns:
            The configuration type
        """

        return GeneratorPluginGroupData

    @pytest.fixture(name="plugin_group_data", scope="session")
    def fixture_plugin_group_data(
        self, project_data: ProjectData, cppython_plugin_data: CPPythonPluginData
    ) -> GeneratorPluginGroupData:
        """Generates plugin configuration data generation from environment configuration

        Args:
            project_data: The project data fixture
            cppython_plugin_data:The plugin configuration fixture

        Returns:
            The plugin configuration
        """

        return resolve_generator(project_data=project_data, cppython_data=cppython_plugin_data)

    @pytest.fixture(
        name="provider_type",
        scope="session",
        params=provider_variants,
    )
    def fixture_provider_type(self, request: pytest.FixtureRequest) -> type[Provider]:
        """Fixture defining all testable variations mock Providers

        Args:
            request: Parameterization list

        Returns:
            Variation of a Provider
        """
        provider_type = cast(type[Provider], request.param)

        return provider_type

    @pytest.fixture(
        name="generator_type",
        scope="session",
    )
    def fixture_generator_type(self, plugin_type: type[T]) -> type[T]:
        """Override

        Args:
            plugin_type: Plugin type

        Returns:
            Plugin type
        """

        return plugin_type

    @pytest.fixture(
        name="scm_type",
        scope="session",
        params=scm_variants,
    )
    def fixture_scm_type(self, request: pytest.FixtureRequest) -> type[SCM]:
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

    @pytest.fixture(name="plugin_configuration_type", scope="session")
    def fixture_plugin_configuration_type(self) -> type[SCMPluginGroupData]:
        """A required testing hook that allows plugin configuration data generation

        Returns:
            The configuration type
        """

        return SCMPluginGroupData

    @pytest.fixture(name="plugin_group_data", scope="session")
    def fixture_plugin_group_data(
        self, project_data: ProjectData, cppython_plugin_data: CPPythonPluginData
    ) -> SCMPluginGroupData:
        """Generates plugin configuration data generation from environment configuration

        Args:
            project_data: The project data fixture
            cppython_plugin_data:The plugin configuration fixture

        Returns:
            The plugin configuration
        """

        return resolve_scm(project_data=project_data, cppython_data=cppython_plugin_data)

    @pytest.fixture(
        name="provider_type",
        scope="session",
        params=provider_variants,
    )
    def fixture_provider_type(self, request: pytest.FixtureRequest) -> type[Provider]:
        """Fixture defining all testable variations mock Providers

        Args:
            request: Parameterization list

        Returns:
            Variation of a Provider
        """
        provider_type = cast(type[Provider], request.param)

        return provider_type

    @pytest.fixture(
        name="generator_type",
        scope="session",
        params=generator_variants,
    )
    def fixture_generator_type(self, request: pytest.FixtureRequest) -> type[Generator]:
        """Fixture defining all testable variations mock Generator

        Args:
            request: Parameterization list

        Returns:
            Variation of a Generator
        """
        generator_type = cast(type[Generator], request.param)

        return generator_type

    @pytest.fixture(
        name="scm_type",
        scope="session",
        params=scm_variants,
    )
    def fixture_scm_type(self, plugin_type: type[T]) -> type[SCM]:
        """Fixture defining all testable variations mock Generator

        Args:
            plugin_type: Parameterization list

        Returns:
            Variation of a Generator
        """

        return plugin_type
