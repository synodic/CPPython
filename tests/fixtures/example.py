"""Fixtures for the cmake plugin"""

import os
import shutil
from collections.abc import Generator
from pathlib import Path
from typing import cast

import pytest
from typer.testing import CliRunner

pytest_plugins = ['tests.fixtures.cli']


def _examples() -> list[Path]:
    """Returns the examples directory"""
    matching_directories = []

    for dirpath, _, filenames in os.walk('examples'):
        for filename in filenames:
            if filename == 'pyproject.toml':
                absolute_path = Path(dirpath).absolute()
                matching_directories.append(absolute_path)
                break

    return matching_directories


@pytest.fixture(
    name='example_directory',
    scope='session',
    params=_examples(),
)
def fixture_example_directory(
    request: pytest.FixtureRequest,
) -> Path:
    """Enumerates folders in the examples directory.

    Parameterizes all directories with a pyproject.toml file within the examples directory.
    """
    directory = cast(Path, request.param)
    return directory


@pytest.fixture(
    name='example_runner',
)
def fixture_example_runner(
    request: pytest.FixtureRequest, typer_runner: CliRunner, tmp_path: Path
) -> Generator[CliRunner]:
    """Sets up an isolated filesystem for an example test."""
    # Get the root directory of the project
    root_directory = Path(__file__).parent.parent.parent.absolute()

    # Remove the file extension and required 'test_' prefix from the test's file name
    file_name = request.node.fspath.basename[:-3].replace('test_', '')

    # Get the test function name and remove the required 'test_' prefix
    test_name = request.node.name.replace('test_', '')

    # Generate the example path from the pytest file and test name
    example_path = root_directory / 'examples' / file_name / test_name

    with typer_runner.isolated_filesystem(temp_dir=tmp_path):
        # Copy the example directory to the temporary directory
        shutil.copytree(example_path, Path(), dirs_exist_ok=True)

        yield typer_runner
