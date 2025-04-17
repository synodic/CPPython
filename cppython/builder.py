"""Defines the data and routines for building a CPPython project type"""

import logging
from importlib.metadata import entry_points
from inspect import getmodule
from logging import Logger
from typing import Any, cast

from cppython.core.plugin_schema.generator import Generator
from cppython.core.plugin_schema.provider import Provider
from cppython.core.plugin_schema.scm import SCM, SupportedSCMFeatures
from cppython.core.resolution import (
    PluginBuildData,
    PluginCPPythonData,
    resolve_cppython,
    resolve_cppython_plugin,
    resolve_generator,
    resolve_pep621,
    resolve_project_configuration,
    resolve_provider,
    resolve_scm,
)
from cppython.core.schema import (
    CoreData,
    CorePluginData,
    CPPythonGlobalConfiguration,
    CPPythonLocalConfiguration,
    DataPlugin,
    PEP621Configuration,
    PEP621Data,
    ProjectConfiguration,
    ProjectData,
)
from cppython.data import Data, Plugins
from cppython.defaults import DefaultSCM
from cppython.utility.exception import PluginError


class Resolver:
    """The resolution of data sources for the builder"""

    def __init__(self, project_configuration: ProjectConfiguration, logger: Logger) -> None:
        """Initializes the resolver"""
        self._project_configuration = project_configuration
        self._logger = logger

    def generate_plugins(
        self, cppython_local_configuration: CPPythonLocalConfiguration, project_data: ProjectData
    ) -> PluginBuildData:
        """Generates the plugin data from the local configuration and project data

        Args:
            cppython_local_configuration: The local configuration
            project_data: The project data

        Returns:
            The resolved plugin data
        """
        raw_generator_plugins = self.find_generators()
        generator_plugins = self.filter_plugins(
            raw_generator_plugins,
            cppython_local_configuration.generator_name,
            'Generator',
        )

        raw_provider_plugins = self.find_providers()
        provider_plugins = self.filter_plugins(
            raw_provider_plugins,
            cppython_local_configuration.provider_name,
            'Provider',
        )

        scm_plugins = self.find_source_managers()

        scm_type = self.select_scm(scm_plugins, project_data)

        # Solve the messy interactions between plugins
        generator_type, provider_type = self.solve(generator_plugins, provider_plugins)

        return PluginBuildData(generator_type=generator_type, provider_type=provider_type, scm_type=scm_type)

    @staticmethod
    def generate_cppython_plugin_data(plugin_build_data: PluginBuildData) -> PluginCPPythonData:
        """Generates the CPPython plugin data from the resolved plugins

        Args:
            plugin_build_data: The resolved plugin data

        Returns:
            The plugin data used by CPPython
        """
        return PluginCPPythonData(
            generator_name=plugin_build_data.generator_type.name(),
            provider_name=plugin_build_data.provider_type.name(),
            scm_name=plugin_build_data.scm_type.name(),
        )

    @staticmethod
    def generate_pep621_data(
        pep621_configuration: PEP621Configuration, project_configuration: ProjectConfiguration, scm: SCM | None
    ) -> PEP621Data:
        """Generates the PEP621 data from configuration sources

        Args:
            pep621_configuration: The PEP621 configuration
            project_configuration: The project configuration
            scm: The source control manager, if any

        Returns:
            The resolved PEP621 data
        """
        return resolve_pep621(pep621_configuration, project_configuration, scm)

    @staticmethod
    def resolve_global_config() -> CPPythonGlobalConfiguration:
        """Generates the global configuration object

        Returns:
            The global configuration object
        """
        return CPPythonGlobalConfiguration()

    def find_generators(self) -> list[type[Generator]]:
        """Extracts the generator plugins from the package's entry points

        Raises:
            PluginError: Raised if no plugins can be found

        Returns:
            The list of generator plugin types
        """
        group_name = 'generator'
        plugin_types: list[type[Generator]] = []

        entries = entry_points(group=f'cppython.{group_name}')

        # Filter entries by type
        for entry_point in list(entries):
            loaded_type = entry_point.load()
            if not issubclass(loaded_type, Generator):
                self._logger.warning(
                    f"Found incompatible plugin. The '{loaded_type.name()}' plugin must be an instance of"
                    f" '{group_name}'"
                )
            else:
                self._logger.info(f'{group_name} plugin found: {loaded_type.name()} from {getmodule(loaded_type)}')
                plugin_types.append(loaded_type)

        if not plugin_types:
            raise PluginError(f'No {group_name} plugin was found')

        return plugin_types

    def find_providers(self) -> list[type[Provider]]:
        """Extracts the provider plugins from the package's entry points

        Raises:
            PluginError: Raised if no plugins can be found

        Returns:
            The list of provider plugin types
        """
        group_name = 'provider'
        plugin_types: list[type[Provider]] = []

        entries = entry_points(group=f'cppython.{group_name}')

        # Filter entries by type
        for entry_point in list(entries):
            loaded_type = entry_point.load()
            if not issubclass(loaded_type, Provider):
                self._logger.warning(
                    f"Found incompatible plugin. The '{loaded_type.name()}' plugin must be an instance of"
                    f" '{group_name}'"
                )
            else:
                self._logger.info(f'{group_name} plugin found: {loaded_type.name()} from {getmodule(loaded_type)}')
                plugin_types.append(loaded_type)

        if not plugin_types:
            raise PluginError(f'No {group_name} plugin was found')

        return plugin_types

    def find_source_managers(self) -> list[type[SCM]]:
        """Extracts the source control manager plugins from the package's entry points

        Raises:
            PluginError: Raised if no plugins can be found

        Returns:
            The list of source control manager plugin types
        """
        group_name = 'scm'
        plugin_types: list[type[SCM]] = []

        entries = entry_points(group=f'cppython.{group_name}')

        # Filter entries by type
        for entry_point in list(entries):
            loaded_type = entry_point.load()
            if not issubclass(loaded_type, SCM):
                self._logger.warning(
                    f"Found incompatible plugin. The '{loaded_type.name()}' plugin must be an instance of"
                    f" '{group_name}'"
                )
            else:
                self._logger.info(f'{group_name} plugin found: {loaded_type.name()} from {getmodule(loaded_type)}')
                plugin_types.append(loaded_type)

        if not plugin_types:
            raise PluginError(f'No {group_name} plugin was found')

        return plugin_types

    def filter_plugins[T: DataPlugin](
        self, plugin_types: list[type[T]], pinned_name: str | None, group_name: str
    ) -> list[type[T]]:
        """Finds and filters data plugins

        Args:
            plugin_types: The plugin type to lookup
            pinned_name: The configuration name
            group_name: The group name

        Raises:
            PluginError: Raised if no plugins can be found

        Returns:
            The list of applicable plugins
        """
        # Lookup the requested plugin if given
        if pinned_name is not None:
            for loaded_type in plugin_types:
                if loaded_type.name() == pinned_name:
                    self._logger.info(f'Using {group_name} plugin: {loaded_type.name()} from {getmodule(loaded_type)}')
                    return [loaded_type]

        self._logger.info(f"'{group_name}_name' was empty. Trying to deduce {group_name}s")

        supported_types: list[type[T]] = []

        # Deduce types
        for loaded_type in plugin_types:
            self._logger.info(f'A {group_name} plugin is supported: {loaded_type.name()} from {getmodule(loaded_type)}')
            supported_types.append(loaded_type)

        # Fail
        if supported_types is None:
            raise PluginError(f'No {group_name} could be deduced from the root directory.')

        return supported_types

    def select_scm(self, scm_plugins: list[type[SCM]], project_data: ProjectData) -> type[SCM]:
        """Given data constraints, selects the SCM plugin to use

        Args:
            scm_plugins: The list of SCM plugin types
            project_data: The project data

        Returns:
            The selected SCM plugin type
        """
        for scm_type in scm_plugins:
            if cast(SupportedSCMFeatures, scm_type.features(project_data.project_root)).repository:
                return scm_type

        self._logger.info('No SCM plugin was found that supports the given path')

        return DefaultSCM

    @staticmethod
    def solve(
        generator_types: list[type[Generator]], provider_types: list[type[Provider]]
    ) -> tuple[type[Generator], type[Provider]]:
        """Selects the first generator and provider that can work together

        Args:
            generator_types: The list of generator plugin types
            provider_types: The list of provider plugin types

        Raises:
            PluginError: Raised if no provider that supports a given generator could be deduced

        Returns:
            A tuple of the selected generator and provider plugin types
        """
        combos: list[tuple[type[Generator], type[Provider]]] = []

        for generator_type in generator_types:
            sync_types = generator_type.sync_types()
            for provider_type in provider_types:
                for sync_type in sync_types:
                    if provider_type.supported_sync_type(sync_type):
                        combos.append((generator_type, provider_type))
                        break

        if not combos:
            raise PluginError('No provider that supports a given generator could be deduced')

        return combos[0]

    @staticmethod
    def create_scm(
        core_data: CoreData,
        scm_type: type[SCM],
    ) -> SCM:
        """Creates a source control manager from input configuration

        Args:
            core_data: The resolved configuration data
            scm_type: The plugin type

        Returns:
            The constructed source control manager
        """
        cppython_plugin_data = resolve_cppython_plugin(core_data.cppython_data, scm_type)
        scm_data = resolve_scm(core_data.project_data, cppython_plugin_data)

        plugin = cast(SCM, scm_type(scm_data))

        return plugin

    def create_generator(
        self,
        core_data: CoreData,
        pep621_data: PEP621Data,
        generator_configuration: dict[str, Any],
        generator_type: type[Generator],
    ) -> Generator:
        """Creates a generator from input configuration

        Args:
            core_data: The resolved configuration data
            pep621_data: The PEP621 data
            generator_configuration: The generator table of the CPPython configuration data
            generator_type: The plugin type

        Returns:
            The constructed generator
        """
        cppython_plugin_data = resolve_cppython_plugin(core_data.cppython_data, generator_type)

        generator_data = resolve_generator(core_data.project_data, cppython_plugin_data)

        if not generator_configuration:
            self._logger.info(
                "The pyproject.toml table 'tool.cppython.generator' does not exist. Sending generator empty data",
            )

        core_plugin_data = CorePluginData(
            project_data=core_data.project_data,
            pep621_data=pep621_data,
            cppython_data=cppython_plugin_data,
        )

        return cast(Generator, generator_type(generator_data, core_plugin_data, generator_configuration))

    def create_provider(
        self,
        core_data: CoreData,
        pep621_data: PEP621Data,
        provider_configuration: dict[str, Any],
        provider_type: type[Provider],
    ) -> Provider:
        """Creates Providers from input data

        Args:
            core_data: The resolved configuration data
            pep621_data: The PEP621 data
            provider_configuration: The provider data table
            provider_type: The type to instantiate

        Returns:
            A constructed provider plugins
        """
        cppython_plugin_data = resolve_cppython_plugin(core_data.cppython_data, provider_type)

        provider_data = resolve_provider(core_data.project_data, cppython_plugin_data)

        if not provider_configuration:
            self._logger.info(
                "The pyproject.toml table 'tool.cppython.provider' does not exist. Sending provider empty data",
            )

        core_plugin_data = CorePluginData(
            project_data=core_data.project_data,
            pep621_data=pep621_data,
            cppython_data=cppython_plugin_data,
        )

        return cast(Provider, provider_type(provider_data, core_plugin_data, provider_configuration))


class Builder:
    """Helper class for building CPPython projects"""

    levels = [logging.WARNING, logging.INFO, logging.DEBUG]

    def __init__(self, project_configuration: ProjectConfiguration, logger: Logger) -> None:
        """Initializes the builder"""
        self._project_configuration = project_configuration
        self._logger = logger

        # Add default output stream
        self._logger.addHandler(logging.StreamHandler())
        self._logger.setLevel(Builder.levels[project_configuration.verbosity])

        self._logger.info('Logging setup complete')

        self._resolver = Resolver(self._project_configuration, self._logger)

    def build(
        self,
        pep621_configuration: PEP621Configuration,
        cppython_local_configuration: CPPythonLocalConfiguration,
        plugin_build_data: PluginBuildData | None = None,
    ) -> Data:
        """Builds the project data

        Args:
            pep621_configuration: The PEP621 configuration
            cppython_local_configuration: The local configuration
            plugin_build_data: Plugin override data. If it exists, the build will use the given types
                instead of resolving them

        Returns:
            The built data object
        """
        project_data = resolve_project_configuration(self._project_configuration)

        if plugin_build_data is None:
            plugin_build_data = self._resolver.generate_plugins(cppython_local_configuration, project_data)

        plugin_cppython_data = self._resolver.generate_cppython_plugin_data(plugin_build_data)

        global_configuration = self._resolver.resolve_global_config()

        cppython_data = resolve_cppython(
            cppython_local_configuration, global_configuration, project_data, plugin_cppython_data
        )

        core_data = CoreData(project_data=project_data, cppython_data=cppython_data)

        scm = self._resolver.create_scm(core_data, plugin_build_data.scm_type)

        pep621_data = self._resolver.generate_pep621_data(pep621_configuration, self._project_configuration, scm)

        # Create the chosen plugins
        generator = self._resolver.create_generator(
            core_data, pep621_data, cppython_local_configuration.generator, plugin_build_data.generator_type
        )
        provider = self._resolver.create_provider(
            core_data, pep621_data, cppython_local_configuration.provider, plugin_build_data.provider_type
        )

        plugins = Plugins(generator=generator, provider=provider, scm=scm)

        return Data(core_data, plugins, self._logger)
