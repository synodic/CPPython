"""A click CLI for CPPython interfacing"""

import tomllib
from logging import getLogger
from pathlib import Path

import click

from cppython.core.schema import Interface, ProjectConfiguration
from cppython.project import Project


def _find_pyproject_file() -> Path:
    """Searches upward for a pyproject.toml file

    Returns:
        The found directory
    """

    # Search for a path upward
    path = Path.cwd()

    while not path.glob("pyproject.toml"):
        if path.is_absolute():
            assert (
                False
            ), "This is not a valid project. No pyproject.toml found in the current directory or any of its parents."

    path = Path(path)

    return path


class Configuration:
    """Click configuration object"""

    def __init__(self) -> None:
        self.interface = ConsoleInterface()

        self.logger = getLogger("cppython.console")

        path = _find_pyproject_file()
        file_path = path / "pyproject.toml"

        self.configuration = ProjectConfiguration(pyproject_file=file_path, version=None)

    def query_scm(self) -> str:
        """Queries the SCM system for its version

        Returns:
            The version
        """

        return "TODO"

    def generate_project(self) -> Project:
        """Aids in project generation. Allows deferred configuration from within the "config" object

        Returns:
            The constructed Project
        """

        path = self.configuration.pyproject_file
        pyproject_data = tomllib.loads(path.read_text(encoding="utf-8"))

        return Project(self.configuration, self.interface, pyproject_data)


# Attach our config object to click's hook
pass_config = click.make_pass_decorator(Configuration, ensure=True)


@click.group()
@click.option("-v", "--verbose", count=True, help="Print additional output")
@click.option("--debug/--no-debug", default=False)
@pass_config
def cli(config: Configuration, verbose: int, debug: bool) -> None:
    """entry_point group for the CLI commands

    Args:
        config: The CLI configuration object
        verbose: The verbosity level
        debug: Debug mode
    """
    config.configuration.verbosity = verbose
    config.configuration.debug = debug


@cli.command(name="info")
@pass_config
def info_command(config: Configuration) -> None:
    """Prints project information

    Args:
        config: The CLI configuration object
    """

    version = config.query_scm()
    config.logger.info("The SCM project version is: %s", version)


@cli.command(name="list")
@pass_config
def list_command(config: Configuration) -> None:
    """Prints project information

    Args:
        config: The CLI configuration object
    """

    version = config.query_scm()
    config.logger.info("The SCM project version is: %s", version)


@cli.command(name="install")
@pass_config
def install_command(config: Configuration) -> None:
    """Install API call

    Args:
        config: The CLI configuration object
    """
    project = config.generate_project()
    project.install()


@cli.command(name="update")
@pass_config
def update_command(config: Configuration) -> None:
    """Update API call

    Args:
        config: The CLI configuration object
    """
    project = config.generate_project()
    project.update()


class ConsoleInterface(Interface):
    """Interface implementation to pass to the project"""

    def write_pyproject(self) -> None:
        """Write output"""

    def write_configuration(self) -> None:
        """Write output"""
