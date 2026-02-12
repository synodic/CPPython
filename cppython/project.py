"""Manages data flow to and from plugins"""

import asyncio
import logging
from typing import Any

from cppython.builder import Builder
from cppython.core.exception import ConfigException
from cppython.core.resolution import resolve_model
from cppython.core.schema import Interface, ProjectConfiguration, PyProject, SyncData
from cppython.schema import API


class Project(API):
    """The object that should be constructed at each entry_point"""

    def __init__(
        self, project_configuration: ProjectConfiguration, interface: Interface, pyproject_data: dict[str, Any]
    ) -> None:
        """Initializes the project

        Args:
            project_configuration: Project-wide configuration
            interface: Interface for callbacks to write configuration changes
            pyproject_data: Merged configuration data from all sources
        """
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

    def install(self, groups: list[str] | None = None) -> None:
        """Installs project dependencies

        Args:
            groups: Optional list of dependency groups to install in addition to base dependencies

        Raises:
            Exception: Provider-specific exceptions are propagated with full context
        """
        if not self._enabled:
            self.logger.info('Skipping install because the project is not enabled')
            return

        self.logger.info('Installing tools')
        asyncio.run(self._data.download_provider_tools())

        self.logger.info('Installing project')

        # Log active groups
        if groups:
            self.logger.info('Installing with dependency groups: %s', ', '.join(groups))

        self.logger.info('Installing %s provider', self._data.plugins.provider.name())

        # Validate and log active groups
        self._data.apply_dependency_groups(groups)

        # Sync before install to allow provider to access generator's resolved configuration
        self._data.sync()

        # Let provider handle its own exceptions for better error context
        self._data.plugins.provider.install(groups=groups)

    def update(self, groups: list[str] | None = None) -> None:
        """Updates project dependencies

        Args:
            groups: Optional list of dependency groups to update in addition to base dependencies

        Raises:
            Exception: Provider-specific exception
        """
        if not self._enabled:
            self.logger.info('Skipping update because the project is not enabled')
            return

        self.logger.info('Updating tools')
        asyncio.run(self._data.download_provider_tools())

        self.logger.info('Updating project')

        # Log active groups
        if groups:
            self.logger.info('Updating with dependency groups: %s', ', '.join(groups))

        self.logger.info('Updating %s provider', self._data.plugins.provider.name())

        # Validate and log active groups
        self._data.apply_dependency_groups(groups)

        # Sync before update to allow provider to access generator's resolved configuration
        self._data.sync()

        # Let provider handle its own exceptions for better error context
        self._data.plugins.provider.update(groups=groups)

    def publish(self) -> None:
        """Publishes the project

        Raises:
            Exception: Provider-specific exception
        """
        if not self._enabled:
            self.logger.info('Skipping publish because the project is not enabled')
            return

        self.logger.info('Publishing project')

        # Ensure sync is performed before publishing to generate necessary files
        self._data.sync()

        # Let provider handle its own exceptions for better error context
        self._data.plugins.provider.publish()

    def prepare_build(self) -> SyncData | None:
        """Prepare for a PEP 517 build without installing C++ dependencies.

        Syncs generated files (presets, native files) and verifies that a prior
        ``install()`` call has produced the expected provider artifacts. This is
        used by the build backend so that ``pdm build`` / ``pip wheel`` can
        delegate to scikit-build-core or meson-python without re-running the
        full provider install workflow.

        Returns:
            The sync data from the provider, or None if the project is not enabled

        Raises:
            InstallationVerificationError: If provider artifacts are missing
        """
        if not self._enabled:
            self.logger.info('Skipping prepare_build because the project is not enabled')
            return None

        self.logger.info('Preparing build environment')

        # Sync config files so the generator has up-to-date presets / native files
        self._data.sync()

        # Verify that a prior install() produced the expected artifacts
        self._data.plugins.provider.verify_installed()

        # Return sync data for the build backend to inject into config_settings
        return self._data.plugins.provider.sync_data(self._data.plugins.generator)

    def build(self, configuration: str | None = None) -> None:
        """Builds the project

        Assumes dependencies have been installed via `install`.
        Syncs generated files to ensure they are up-to-date, then executes the build.

        Args:
            configuration: Optional named configuration to use
        """
        if not self._enabled:
            self.logger.info('Skipping build because the project is not enabled')
            return

        self.logger.info('Building project')
        self._data.sync()
        self._data.plugins.generator.build(configuration=configuration)

    def test(self, configuration: str | None = None) -> None:
        """Runs project tests

        Assumes dependencies have been installed via `install`.
        Syncs generated files to ensure they are up-to-date, then executes tests.

        Args:
            configuration: Optional named configuration to use
        """
        if not self._enabled:
            self.logger.info('Skipping test because the project is not enabled')
            return

        self.logger.info('Running tests')
        self._data.sync()
        self._data.plugins.generator.test(configuration=configuration)

    def bench(self, configuration: str | None = None) -> None:
        """Runs project benchmarks

        Assumes dependencies have been installed via `install`.
        Syncs generated files to ensure they are up-to-date, then executes benchmarks.

        Args:
            configuration: Optional named configuration to use
        """
        if not self._enabled:
            self.logger.info('Skipping bench because the project is not enabled')
            return

        self.logger.info('Running benchmarks')
        self._data.sync()
        self._data.plugins.generator.bench(configuration=configuration)

    def run(self, target: str, configuration: str | None = None) -> None:
        """Runs a built executable

        Assumes dependencies have been installed via `install`.
        Syncs generated files to ensure they are up-to-date, then executes the target.

        Args:
            target: The name of the build target to run
            configuration: Optional named configuration to use
        """
        if not self._enabled:
            self.logger.info('Skipping run because the project is not enabled')
            return

        self.logger.info('Running target: %s', target)
        self._data.sync()
        self._data.plugins.generator.run(target, configuration=configuration)
