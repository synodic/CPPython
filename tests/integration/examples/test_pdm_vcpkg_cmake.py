"""Example folder tests.

All examples can be run with the CPPython entry-point, and we use the examples as the test data for the CLI.
"""

import shutil
from pathlib import Path

from cppython.utility.filesystem import isolated_filesystem

pytest_plugins = ['tests.fixtures.cmake']


class TestSetup:
    """Verification that the example directory is setup correctly"""

    @staticmethod
    def test_example_directory(example_directory: Path) -> None:
        """Verify that the fixture is returning the right data"""
        assert example_directory.is_dir()
        assert (example_directory / 'pyproject.toml').is_file()

    @staticmethod
    def test_list(example_directory: Path) -> None:
        """Verifies that the list command functions with CPPython hooks"""
        with isolated_filesystem() as temp_directory:
            shutil.copytree(example_directory, temp_directory, dirs_exist_ok=True)

            # result = runner.invoke(app, ['list'])
            # assert result.exit_code == 0
