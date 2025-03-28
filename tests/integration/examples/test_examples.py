"""Example folder tests.

All examples can be run with the CPPython entry-point, and we use the examples as the test data for the CLI.
"""

from pathlib import Path

pytest_plugins = ['tests.fixtures.example']


class TestExamples:
    """Verification that the example directory is setup correctly"""

    @staticmethod
    def test_example_directory(example_directory: Path) -> None:
        """Verify that the fixture is returning the right data"""
        assert example_directory.is_dir()
        assert (example_directory / 'pyproject.toml').is_file()
