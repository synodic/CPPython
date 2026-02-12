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

from cppython.core.interface import NoOpInterface
from cppython.core.schema import ProjectConfiguration, SyncData
from cppython.project import Project
from cppython.utility.exception import InstallationVerificationError


@dataclass
class BuildPreparationResult:
    """Result of the build preparation step.

    Contains the sync data from the provider, which the build backend
    uses to determine which underlying backend to delegate to and what
    configuration to inject.
    """

    sync_data: SyncData | None = None


BuildInterface = NoOpInterface
"""Interface implementation for the build backend (no-op write-backs)."""


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

    def prepare(self) -> BuildPreparationResult:
        """Run CPPython preparation and return the build preparation result.

        Syncs provider config and verifies that C++ dependencies have been
        installed by a prior ``install()`` call. Does **not** install
        dependencies itself — the build backend is not responsible for that.

        Returns:
            BuildPreparationResult containing sync data for the active generator

        Raises:
            InstallationVerificationError: If provider artifacts are missing
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

        # Sync and verify — does NOT install dependencies
        self.logger.info('CPPython: Verifying C++ dependencies are installed')

        try:
            sync_data = project.prepare_build()
        except InstallationVerificationError:
            self.logger.error(
                "CPPython: C++ dependencies not installed. Run 'cppython install' or 'pdm install' before building."
            )
            raise

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
