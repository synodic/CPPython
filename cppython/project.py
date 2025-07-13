"""Manages data flow to and from plugins"""

import asyncio
import logging
from typing import Any

from cppython.builder import Builder
from cppython.core.exception import ConfigException
from cppython.core.resolution import resolve_model
from cppython.core.schema import Interface, ProjectConfiguration, PyProject
from cppython.schema import API


class Project(API):
    """The object that should be constructed at each entry_point"""

    def __init__(
        self, project_configuration: ProjectConfiguration, interface: Interface, pyproject_data: dict[str, Any]
    ) -> None:
        """Initializes the project"""
        self._enabled = False
        self._interface = interface
        self.logger = logging.getLogger('cppython')

        builder = Builder(project_configuration, self.logger)

        self.logger.info('Initializing project')

        try:
            pyproject = resolve_model(PyProject, pyproject_data)
        except ConfigException as error:
            # Log the exception message explicitly
            self.logger.error('Configuration error:\n%s', error, exc_info=False)
            raise SystemExit('Error: Invalid configuration. Please check your pyproject.toml.') from None

        if not pyproject.tool or not pyproject.tool.cppython:
            self.logger.info("The pyproject.toml file doesn't contain the `tool.cppython` table")
            return

        self._data = builder.build(pyproject.project, pyproject.tool.cppython)

        self._enabled = True

        self.logger.info('Initialized project successfully')

    @property
    def enabled(self) -> bool:
        """Queries if the project was is initialized for full functionality

        Returns:
            The query result
        """
        return self._enabled

    def install(self) -> None:
        """Installs project dependencies

        Raises:
            Exception: Provider-specific exceptions are propagated with full context
        """
        if not self._enabled:
            self.logger.info('Skipping install because the project is not enabled')
            return

        self.logger.info('Installing tools')
        asyncio.run(self._data.download_provider_tools())

        self.logger.info('Installing project')
        self.logger.info('Installing %s provider', self._data.plugins.provider.name())

        # Let provider handle its own exceptions for better error context
        self._data.plugins.provider.install()
        self._data.sync()

    def update(self) -> None:
        """Updates project dependencies

        Raises:
            Exception: Provider-specific exception
        """
        if not self._enabled:
            self.logger.info('Skipping update because the project is not enabled')
            return

        self.logger.info('Updating tools')
        asyncio.run(self._data.download_provider_tools())

        self.logger.info('Updating project')
        self.logger.info('Updating %s provider', self._data.plugins.provider.name())

        # Let provider handle its own exceptions for better error context
        self._data.plugins.provider.update()
        self._data.sync()

    def publish(self) -> None:
        """Publishes the project

        Raises:
            Exception: Provider-specific exception
        """
        # Let provider handle its own exceptions for better error context
        self._data.plugins.provider.publish()
