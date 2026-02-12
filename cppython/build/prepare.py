"""Build preparation utilities for CPPython.

This module handles the pre-build workflow: running CPPython's provider
to install C++ dependencies and extract sync data for injection into
the appropriate build backend (scikit-build-core or meson-python).
"""

import logging
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cppython.core.schema import Interface, ProjectConfiguration, SyncData
from cppython.project import Project


@dataclass
class BuildPreparationResult:
    """Result of the build preparation step.

    Contains the sync data from the provider, which the build backend
    uses to determine which underlying backend to delegate to and what
    configuration to inject.
    """

    sync_data: SyncData | None = None


class BuildInterface(Interface):
    """Minimal interface implementation for build backend usage."""

    def write_pyproject(self) -> None:
        """No-op for build backend - we don't modify pyproject.toml during builds."""

    def write_configuration(self) -> None:
        """No-op for build backend - we don't modify configuration during builds."""

    def write_user_configuration(self) -> None:
        """No-op for build backend - we don't modify user configuration during builds."""


class BuildPreparation:
    """Handles CPPython preparation before the build backend runs."""

    def __init__(self, source_dir: Path) -> None:
        """Initialize build preparation.

        Args:
            source_dir: The source directory containing pyproject.toml
        """
        self.source_dir = source_dir.absolute()
        self.logger = logging.getLogger('cppython.build')

    def _load_pyproject(self) -> dict[str, Any]:
        """Load pyproject.toml from the source directory.

        Returns:
            The parsed pyproject.toml contents

        Raises:
            FileNotFoundError: If pyproject.toml doesn't exist
        """
        pyproject_path = self.source_dir / 'pyproject.toml'
        if not pyproject_path.exists():
            raise FileNotFoundError(f'pyproject.toml not found at {pyproject_path}')

        with open(pyproject_path, 'rb') as f:
            return tomllib.load(f)

    def _get_sync_data(self, project: Project) -> SyncData | None:
        """Extract sync data from the project's provider for the active generator.

        Args:
            project: The initialized CPPython project

        Returns:
            The sync data from the provider, or None if not available
        """
        if not project.enabled:
            return None

        # Access the internal data to get sync information
        data = project._data  # noqa: SLF001

        # Get sync data from provider for the generator
        return data.plugins.provider.sync_data(data.plugins.generator)

    def prepare(self) -> BuildPreparationResult:
        """Run CPPython preparation and return the build preparation result.

        This runs the provider workflow (download tools, sync, install)
        and extracts the sync data for injection into the build backend.

        Returns:
            BuildPreparationResult containing sync data for the active generator
        """
        self.logger.info('CPPython: Preparing build environment')

        pyproject_data = self._load_pyproject()

        # Check if CPPython is configured
        tool_data = pyproject_data.get('tool', {})
        if 'cppython' not in tool_data:
            self.logger.info('CPPython: No [tool.cppython] configuration found, skipping preparation')
            return BuildPreparationResult()

        # Get version from pyproject if available
        project_data = pyproject_data.get('project', {})
        version = project_data.get('version')

        # Create project configuration
        project_config = ProjectConfiguration(
            project_root=self.source_dir,
            version=version,
            verbosity=1,
        )

        # Create the CPPython project
        interface = BuildInterface()
        project = Project(project_config, interface, pyproject_data)

        if not project.enabled:
            self.logger.info('CPPython: Project not enabled, skipping preparation')
            return BuildPreparationResult()

        # Run the install workflow to ensure dependencies are ready
        self.logger.info('CPPython: Installing C++ dependencies')
        project.install()

        # Extract sync data
        sync_data = self._get_sync_data(project)

        if sync_data:
            self.logger.info('CPPython: Sync data obtained from provider: %s', type(sync_data).__name__)
        else:
            self.logger.warning('CPPython: No sync data generated')

        return BuildPreparationResult(sync_data=sync_data)


def prepare_build(source_dir: Path) -> BuildPreparationResult:
    """Convenience function to prepare the build environment.

    Args:
        source_dir: The source directory containing pyproject.toml

    Returns:
        BuildPreparationResult containing sync data for the active generator
    """
    preparation = BuildPreparation(source_dir)
    return preparation.prepare()
