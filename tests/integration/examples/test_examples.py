"""Example folder tests"""

import shutil
from os import walk
from pathlib import Path
from typing import cast

import pytest
from typer.testing import CliRunner

from cppython.console.entry import app

runner = CliRunner()


class TestExamples:
    """Tests to apply to all examples"""

    @staticmethod
    def _examples() -> list[Path]:
        """Returns the examples directory"""
        matching_directories = []

        for dirpath, _, filenames in walk('examples'):
            for filename in filenames:
                if filename == 'pyproject.toml':
                    absolute_path = Path(dirpath).absolute()
                    matching_directories.append(absolute_path)
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
    def test_example_directory(example_directory: Path) -> None:
        """Verify that the fixture is returning the right data"""
        assert example_directory.is_dir()
        assert (example_directory / 'pyproject.toml').is_file()

    @staticmethod
    def test_info(example_directory: Path) -> None:
        """Verifies that the info command functions with CPPython hooks"""
        with runner.isolated_filesystem() as temp_directory:
            shutil.copytree(example_directory, temp_directory, dirs_exist_ok=True)

            result = runner.invoke(app, ['info'])
            assert result.exit_code == 0

    @staticmethod
    def test_list(example_directory: Path) -> None:
        """Verifies that the list command functions with CPPython hooks"""
        with runner.isolated_filesystem() as temp_directory:
            shutil.copytree(example_directory, temp_directory, dirs_exist_ok=True)

            result = runner.invoke(app, ['list'])
            assert result.exit_code == 0

    @staticmethod
    def test_update(example_directory: Path) -> None:
        """Verifies that the update command functions with CPPython hooks"""
        with runner.isolated_filesystem() as temp_directory:
            shutil.copytree(example_directory, temp_directory, dirs_exist_ok=True)

            result = runner.invoke(app, ['update'])
            assert result.exit_code == 0

    @staticmethod
    def test_install(example_directory: Path) -> None:
        """Verifies that the install command functions with CPPython hooks"""
        with runner.isolated_filesystem() as temp_directory:
            shutil.copytree(example_directory, temp_directory, dirs_exist_ok=True)

            result = runner.invoke(app, ['install'])
            assert result.exit_code == 0
