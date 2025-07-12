"""Implementation of the PDM Interface Plugin"""

from argparse import Namespace
from logging import getLogger
from typing import Any

from pdm.cli.commands.base import BaseCommand
from pdm.core import Core
from pdm.project.core import Project
from pdm.signals import post_install

from cppython.console.entry import app
from cppython.core.schema import Interface, ProjectConfiguration
from cppython.project import Project as CPPythonProject


class CPPythonPlugin(Interface):
    """Implementation of the PDM Interface Plugin"""

    def __init__(self, core: Core) -> None:
        """Initializes the plugin"""
        post_install.connect(self.on_post_install, weak=False)
        self.logger = getLogger('cppython.interface.pdm')

        # Register the cpp command
        register_commands(core)

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
        root = project.root.absolute()

        # Attach configuration for CPPythonPlugin callbacks
        version = project.pyproject.metadata.get('version')
        verbosity = project.core.ui.verbosity

        project_configuration = ProjectConfiguration(project_root=root, verbosity=verbosity, version=version)

        self.logger.info("CPPython: Entered 'on_post_install'")

        if (pdm_pyproject := project.pyproject.read()) is None:
            self.logger.info('CPPython: Project data was not available')
            return

        cppython_project = CPPythonProject(project_configuration, self, pdm_pyproject)

        if not dry_run:
            cppython_project.install()


class CPPythonCommand(BaseCommand):
    """PDM command to invoke CPPython directly"""

    name = 'cpp'
    description = 'Run CPPython commands'

    def add_arguments(self, parser) -> None:
        """Add command arguments - delegate to Typer for argument parsing"""
        # Add a catch-all for remaining arguments to pass to Typer
        parser.add_argument('args', nargs='*', help='CPPython command arguments')

    def handle(self, project: Project, options: Namespace) -> None:
        """Handle the command by delegating to the Typer app

        Args:
            project: The PDM project
            options: Command line options
        """
        # Get the command arguments from options
        args = getattr(options, 'args', [])

        try:
            # Invoke cppython directly with the provided arguments
            app(args)
        except SystemExit:
            # Typer/Click uses SystemExit for normal completion, don't propagate it
            pass
        except Exception as e:
            project.core.ui.echo(f'Error running CPPython command: {e}', style='error')


def register_commands(core: Core) -> None:
    """Register the CPPython command with PDM

    Args:
        core: The PDM core instance
    """
    core.register_command(CPPythonCommand)
