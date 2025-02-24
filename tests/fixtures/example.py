"""Fixtures for the cmake plugin"""

import os
from pathlib import Path
from typing import cast

import pytest


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
