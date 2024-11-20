"""Defines the post-construction data management for CPPython"""

from dataclasses import dataclass
from logging import Logger

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

    @property
    def plugins(self) -> Plugins:
        """The plugin data for CPPython"""
        return self._plugins

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
