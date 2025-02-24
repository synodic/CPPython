"""Example folder tests"""

from os import walk
from pathlib import Path
from typing import cast

import pytest


class TestExamples:
    """Tests to apply to all examples"""

    @staticmethod
    def _examples() -> list[Path]:
        """Returns the examples directory"""
        matching_directories = []

        for dirpath, _, filenames in walk('examples'):
            for filename in filenames:
                if filename == 'pyproject.toml':
                    matching_directories.append(Path(dirpath))
                    break

        return matching_directories

    @staticmethod
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

    @staticmethod
    def test_example(example_directory: Path) -> None:
        """Tests the examples"""
        assert example_directory.is_dir()
        assert (example_directory / 'pyproject.toml').is_file()
