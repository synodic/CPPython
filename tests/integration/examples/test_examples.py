"""Example folder tests"""

from pathlib import Path

pytest_plugins = ['tests.fixtures.example']


class TestExamples:
    """Tests to apply to all examples"""

    @staticmethod
    def test_example_directory(example_directory: Path) -> None:
        """Verify that the fixture is returning the right data"""
        assert example_directory.is_dir()
        assert (example_directory / 'pyproject.toml').is_file()
