"""A click CLI for CPPython interfacing"""

from pathlib import Path
from tomllib import loads
from typing import Annotated

import typer
from rich import print

from cppython.console.schema import ConsoleConfiguration, ConsoleInterface
from cppython.core.schema import ProjectConfiguration
from cppython.project import Project

app = typer.Typer(no_args_is_help=True)


def get_enabled_project(context: typer.Context) -> Project:
    """Helper to load and validate an enabled Project from CLI context."""
    configuration = context.find_object(ConsoleConfiguration)
    if configuration is None:
        raise ValueError('The configuration object is missing')

    path = configuration.project_configuration.project_root / 'pyproject.toml'
    pyproject_data = loads(path.read_text(encoding='utf-8'))

    project = Project(configuration.project_configuration, configuration.interface, pyproject_data)
    if not project.enabled:
        print('[bold red]Error[/bold red]: Project is not enabled. Please check your pyproject.toml configuration.')
        raise typer.Exit(code=1)
    return project


def _find_pyproject_file() -> Path:
    """Searches upward for a pyproject.toml file

    Returns:
        The found directory
    """
    # Search for a path upward
    path = Path.cwd()

    while not path.glob('pyproject.toml'):
        if path.is_absolute():
            raise AssertionError(
                'This is not a valid project. No pyproject.toml found in the current directory or any of its parents.'
            )

    path = Path(path)

    return path


@app.callback()
def main(
    context: typer.Context,
    verbose: Annotated[
        int, typer.Option('-v', '--verbose', count=True, min=0, max=2, help='Print additional output')
    ] = 0,
    debug: Annotated[bool, typer.Option()] = False,
) -> None:
    """entry_point group for the CLI commands

    Args:
        context: The typer context
        verbose: The verbosity level
        debug: Debug mode
    """
    path = _find_pyproject_file()

    project_configuration = ProjectConfiguration(verbosity=verbose, debug=debug, project_root=path, version=None)

    interface = ConsoleInterface()
    context.obj = ConsoleConfiguration(project_configuration=project_configuration, interface=interface)


@app.command()
def info(
    _: typer.Context,
) -> None:
    """Prints project information"""


@app.command()
def install(
    context: typer.Context,
) -> None:
    """Install API call

    Args:
        context: The CLI configuration object

    Raises:
        ValueError: If the configuration object is missing
    """
    project = get_enabled_project(context)
    project.install()


@app.command()
def update(
    context: typer.Context,
) -> None:
    """Update API call

    Args:
        context: The CLI configuration object

    Raises:
        ValueError: If the configuration object is missing
    """
    project = get_enabled_project(context)
    project.update()


@app.command(name='list')
def list_command(
    _: typer.Context,
) -> None:
    """Prints project information"""


@app.command()
def publish(
    context: typer.Context,
) -> None:
    """Publish API call

    Args:
        context: The CLI configuration object

    Raises:
        ValueError: If the configuration object is missing
    """
    project = get_enabled_project(context)
    project.publish()
