"""Build preparation utilities for CPPython.

This module handles the pre-build workflow: running CPPython's provider
to install C++ dependencies and extract the toolchain file path for
injection into scikit-build-core's CMake configuration.
"""

import logging
import tomllib
from pathlib import Path
from typing import Any

from cppython.core.schema import Interface, ProjectConfiguration
from cppython.plugins.cmake.schema import CMakeSyncData
from cppython.project import Project


class BuildInterface(Interface):
    """Minimal interface implementation for build backend usage."""

    def write_pyproject(self) -> None:
        """No-op for build backend - we don't modify pyproject.toml during builds."""

    def write_configuration(self) -> None:
        """No-op for build backend - we don't modify configuration during builds."""

    def write_user_configuration(self) -> None:
        """No-op for build backend - we don't modify user configuration during builds."""


class BuildPreparation:
    """Handles CPPython preparation before scikit-build-core runs."""

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

    def _get_toolchain_file(self, project: Project) -> Path | None:
        """Extract the toolchain file path from the project's sync data.

        Args:
            project: The initialized CPPython project

        Returns:
            Path to the toolchain file, or None if not available
        """
        if not project.enabled:
            return None

        # Access the internal data to get sync information
        # The toolchain file is generated during the sync process
        data = project._data  # noqa: SLF001

        # Get sync data from provider for the generator
        sync_data = data.plugins.provider.sync_data(data.plugins.generator)

        if isinstance(sync_data, CMakeSyncData):
            return sync_data.toolchain_file

        return None

    def prepare(self) -> Path | None:
        """Run CPPython preparation and return the toolchain file path.

        This runs the provider workflow (download tools, sync, install)
        and extracts the generated toolchain file path.

        Returns:
            Path to the generated toolchain file, or None if CPPython is not configured
        """
        self.logger.info('CPPython: Preparing build environment')

        pyproject_data = self._load_pyproject()

        # Check if CPPython is configured
        tool_data = pyproject_data.get('tool', {})
        if 'cppython' not in tool_data:
            self.logger.info('CPPython: No [tool.cppython] configuration found, skipping preparation')
            return None

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
            return None

        # Run the install workflow to ensure dependencies are ready
        self.logger.info('CPPython: Installing C++ dependencies')
        project.install()

        # Extract the toolchain file path
        toolchain_file = self._get_toolchain_file(project)

        if toolchain_file:
            self.logger.info('CPPython: Using toolchain file: %s', toolchain_file)
        else:
            self.logger.warning('CPPython: No toolchain file generated')

        return toolchain_file


def prepare_build(source_dir: Path) -> Path | None:
    """Convenience function to prepare the build environment.

    Args:
        source_dir: The source directory containing pyproject.toml

    Returns:
        Path to the generated toolchain file, or None if not available
    """
    preparation = BuildPreparation(source_dir)
    return preparation.prepare()
