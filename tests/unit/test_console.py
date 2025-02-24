"""Tests the typer interface type"""

import shutil
from pathlib import Path

from typer.testing import CliRunner

from cppython.console.entry import app

runner = CliRunner()
pytest_plugins = ['tests.fixtures.example']


class TestConsole:
    """Various that all the examples are accessible to cppython"""

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
