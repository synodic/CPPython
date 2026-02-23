"""A Typer CLI for CPPython interfacing"""

from pathlib import Path
from typing import Annotated

import typer
from rich import print
from rich.syntax import Syntax

from cppython.configuration import ConfigurationLoader
from cppython.console.schema import ConsoleConfiguration, ConsoleInterface
from cppython.core.schema import PluginReport, ProjectConfiguration
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
    """Searches upward for a pyproject.toml file.

    Returns:
        The directory containing pyproject.toml

    Raises:
        AssertionError: If no pyproject.toml is found up to the filesystem root
    """
    path = Path.cwd()

    while True:
        if (path / 'pyproject.toml').exists():
            return path
        parent = path.parent
        if parent == path:
            raise AssertionError(
                'This is not a valid project. No pyproject.toml found in the current directory or any of its parents.'
            )
        path = parent


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
    context: typer.Context,
) -> None:
    """Prints project information including plugin configuration, managed files, and templates."""
    project = get_enabled_project(context)
    project_info = project.info()

    if not project_info:
        return

    for role in ('provider', 'generator'):
        entry = project_info.get(role)
        if entry is None:
            continue

        name: str = entry['name']
        report: PluginReport = entry['report']

        print(f'\n[bold]{role.title()}:[/bold] {name}')

        if report.configuration:
            print('  [bold]Configuration:[/bold]')
            for key, value in report.configuration.items():
                print(f'    {key}: {value}')

        if report.managed_files:
            print('  [bold]Managed files:[/bold]')
            for path in report.managed_files:
                print(f'    {path}')

        if report.template_files:
            print('  [bold]Templates:[/bold]')
            for filename, content in report.template_files.items():
                print(f'    [cyan]{filename}[/cyan]')
                print()
                print(Syntax(content, 'python', theme='monokai', line_numbers=True))


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


@app.command()
def build(
    context: typer.Context,
    configuration: Annotated[
        str | None,
        typer.Option(help='Named build configuration to use (e.g. CMake preset name, Meson build directory)'),
    ] = None,
) -> None:
    """Build the project

    Assumes dependencies have been installed via `install`.

    Args:
        context: The CLI configuration object
        configuration: Optional named configuration
    """
    project = get_enabled_project(context)
    project.build(configuration=configuration)


@app.command()
def test(
    context: typer.Context,
    configuration: Annotated[
        str | None,
        typer.Option(help='Named build configuration to use (e.g. CMake preset name, Meson build directory)'),
    ] = None,
) -> None:
    """Run project tests

    Assumes dependencies have been installed via `install`.

    Args:
        context: The CLI configuration object
        configuration: Optional named configuration
    """
    project = get_enabled_project(context)
    project.test(configuration=configuration)


@app.command()
def bench(
    context: typer.Context,
    configuration: Annotated[
        str | None,
        typer.Option(help='Named build configuration to use (e.g. CMake preset name, Meson build directory)'),
    ] = None,
) -> None:
    """Run project benchmarks

    Assumes dependencies have been installed via `install`.

    Args:
        context: The CLI configuration object
        configuration: Optional named configuration
    """
    project = get_enabled_project(context)
    project.bench(configuration=configuration)


@app.command()
def run(
    context: typer.Context,
    target: Annotated[
        str,
        typer.Argument(help='The name of the build target/executable to run'),
    ],
    configuration: Annotated[
        str | None,
        typer.Option(help='Named build configuration to use (e.g. CMake preset name, Meson build directory)'),
    ] = None,
) -> None:
    """Run a built executable

    Assumes dependencies have been installed via `install`.

    Args:
        context: The CLI configuration object
        target: The name of the build target to run
        configuration: Optional named configuration
    """
    project = get_enabled_project(context)
    project.run(target, configuration=configuration)
