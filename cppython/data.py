"""Defines the post-construction data management for CPPython"""

from dataclasses import dataclass
from logging import Logger

from packaging.requirements import Requirement

from cppython.core.plugin_schema.generator import Generator
from cppython.core.plugin_schema.provider import Provider
from cppython.core.plugin_schema.scm import SCM
from cppython.core.schema import CoreData
from cppython.utility.exception import PluginError


@dataclass
class Plugins:
    """The plugin data for CPPython"""

    generator: Generator
    provider: Provider
    scm: SCM


class Data:
    """Contains and manages the project data"""

    def __init__(self, core_data: CoreData, plugins: Plugins, logger: Logger) -> None:
        """Initializes the data"""
        self._core_data = core_data
        self._plugins = plugins
        self.logger = logger
        self._active_groups: list[str] | None = None

    @property
    def plugins(self) -> Plugins:
        """The plugin data for CPPython"""
        return self._plugins

    def set_active_groups(self, groups: list[str] | None) -> None:
        """Set the active dependency groups for the current operation.

        Args:
            groups: List of group names to activate, or None for no additional groups
        """
        self._active_groups = groups
        if groups:
            self.logger.info('Active dependency groups: %s', ', '.join(groups))

            # Validate that requested groups exist
            available_groups = set(self._core_data.cppython_data.dependency_groups.keys())
            requested_groups = set(groups)
            missing_groups = requested_groups - available_groups

            if missing_groups:
                self.logger.warning(
                    'Requested dependency groups not found: %s. Available groups: %s',
                    ', '.join(sorted(missing_groups)),
                    ', '.join(sorted(available_groups)) if available_groups else 'none',
                )

    def apply_dependency_groups(self, groups: list[str] | None) -> None:
        """Validate and log the dependency groups to be used.

        Args:
            groups: List of group names to apply, or None for base dependencies only
        """
        if groups:
            self.set_active_groups(groups)

    def get_active_dependencies(self) -> list:
        """Get the combined list of base dependencies and active group dependencies.

        Returns:
            Combined list of Requirement objects from base and active groups
        """
        dependencies: list[Requirement] = list(self._core_data.cppython_data.dependencies)

        if self._active_groups:
            for group_name in self._active_groups:
                if group_name in self._core_data.cppython_data.dependency_groups:
                    dependencies.extend(self._core_data.cppython_data.dependency_groups[group_name])

        return dependencies

    def sync(self) -> None:
        """Gathers sync information from providers and passes it to the generator

        Raises:
            PluginError: Plugin error
        """
        if (sync_data := self.plugins.provider.sync_data(self.plugins.generator)) is None:
            raise PluginError("The provider doesn't support the generator")

        self.plugins.generator.sync(sync_data)

    async def download_provider_tools(self) -> None:
        """Download the provider tooling if required"""
        base_path = self._core_data.cppython_data.install_path

        path = base_path / self.plugins.provider.name()

        path.mkdir(parents=True, exist_ok=True)

        self.logger.warning('Downloading the %s requirements to %s', self.plugins.provider.name(), path)
        await self.plugins.provider.download_tooling(path)
