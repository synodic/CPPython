"""Implementation of the PDM Interface Plugin"""

from logging import getLogger
from typing import Any

from pdm.core import Core
from pdm.project.core import Project
from pdm.signals import post_install

from cppython.core.schema import Interface, ProjectConfiguration
from cppython.project import Project as CPPythonProject


class CPPythonPlugin(Interface):
    """Implementation of the PDM Interface Plugin"""

    def __init__(self, _: Core) -> None:
        """Initializes the plugin"""
        post_install.connect(self.on_post_install, weak=False)
        self.logger = getLogger('cppython.interface.pdm')

    def write_pyproject(self) -> None:
        """Write to file"""

    def write_configuration(self) -> None:
        """Write to configuration"""

    def on_post_install(self, project: Project, dry_run: bool, **_kwargs: Any) -> None:
        """Called after a pdm install command is called

        Args:
            project: The input PDM project
            dry_run: If true, won't perform any actions
            _kwargs: Sink for unknown arguments
        """
        pyproject_file = project.root.absolute() / project.PYPROJECT_FILENAME

        # Attach configuration for CPPythonPlugin callbacks
        version = project.pyproject.metadata.get('version')
        verbosity = project.core.ui.verbosity

        project_configuration = ProjectConfiguration(
            pyproject_file=pyproject_file, verbosity=verbosity, version=version
        )

        self.logger.info("CPPython: Entered 'on_post_install'")

        if (pdm_pyproject := project.pyproject.read()) is None:
            self.logger.info('CPPython: Project data was not available')
            return

        cppython_project = CPPythonProject(project_configuration, self, pdm_pyproject)

        if not dry_run:
            cppython_project.install()
