"""A click CLI for CPPython interfacing"""

from pathlib import Path
from typing import Annotated

import typer
from rich import print

from cppython.configuration import ConfigurationLoader
from cppython.console.schema import ConsoleConfiguration, ConsoleInterface
from cppython.core.schema import ProjectConfiguration
from cppython.project import Project

app = typer.Typer(no_args_is_help=True)


def get_enabled_project(context: typer.Context) -> Project:
    """Helper to load and validate an enabled Project from CLI context."""
    configuration = context.find_object(ConsoleConfiguration)
    if configuration is None:
        raise ValueError('The configuration object is missing')

    # Use ConfigurationLoader to load and merge all configuration sources
    loader = ConfigurationLoader(configuration.project_configuration.project_root)
    pyproject_data = loader.get_project_data()

    project = Project(configuration.project_configuration, configuration.interface, pyproject_data)
    if not project.enabled:
        print('[bold red]Error[/bold red]: Project is not enabled. Please check your configuration files.')
        print('Configuration files checked:')
        config_info = loader.config_source_info()
        for config_file, exists in config_info.items():
            status = '✓' if exists else '✗'
            print(f'  {status} {config_file}')
        raise typer.Exit(code=1)
    return project


def _parse_groups_argument(groups: str | None) -> list[str] | None:
    """Parse pip-style dependency groups from command argument.

    Args:
        groups: Groups string like '[test]' or '[dev,test]' or None

    Returns:
        List of group names or None if no groups specified

    Raises:
        typer.BadParameter: If the groups format is invalid
    """
    if groups is None:
        return None

    # Strip whitespace
    groups = groups.strip()

    if not groups:
        return None

    # Check for square brackets
    if not (groups.startswith('[') and groups.endswith(']')):
        raise typer.BadParameter(f"Invalid groups format: '{groups}'. Use square brackets like: [test] or [dev,test]")

    # Extract content between brackets and split by comma
    content = groups[1:-1].strip()

    if not content:
        raise typer.BadParameter('Empty groups specification. Provide at least one group name.')

    # Split by comma and strip whitespace from each group
    group_list = [g.strip() for g in content.split(',')]

    # Validate group names are not empty
    if any(not g for g in group_list):
        raise typer.BadParameter('Group names cannot be empty.')

    return group_list


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
    groups: Annotated[
        str | None,
        typer.Argument(
            help='Dependency groups to install in addition to base dependencies. '
            'Use square brackets like: [test] or [dev,test]'
        ),
    ] = None,
) -> None:
    """Install API call

    Args:
        context: The CLI configuration object
        groups: Optional dependency groups to install (e.g., [test] or [dev,test])

    Raises:
        ValueError: If the configuration object is missing
    """
    project = get_enabled_project(context)

    # Parse groups from pip-style syntax
    group_list = _parse_groups_argument(groups)

    project.install(groups=group_list)


@app.command()
def update(
    context: typer.Context,
    groups: Annotated[
        str | None,
        typer.Argument(
            help='Dependency groups to update in addition to base dependencies. '
            'Use square brackets like: [test] or [dev,test]'
        ),
    ] = None,
) -> None:
    """Update API call

    Args:
        context: The CLI configuration object
        groups: Optional dependency groups to update (e.g., [test] or [dev,test])

    Raises:
        ValueError: If the configuration object is missing
    """
    project = get_enabled_project(context)

    # Parse groups from pip-style syntax
    group_list = _parse_groups_argument(groups)

    project.update(groups=group_list)


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
