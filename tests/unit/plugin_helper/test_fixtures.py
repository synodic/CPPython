"""Tests for fixtures"""

from pathlib import Path


class TestFixtures:
    """Tests for fixtures"""

    def test_data_directory(self, plugin_data_path: Path | None) -> None:
        """Verifies that the directory data provided by pytest_cppython contains a pyproject.toml file

        Args:
            plugin_data_path: The plugins tests/data directory
        """

        assert plugin_data_path is not None
        assert plugin_data_path.exists()

    def test_build_directory(self, build_test_build: Path) -> None:
        """Verifies that the build data provided is the expected path

        Args:
            build_test_build: The plugins build folder directory
        """

        requirement = build_test_build / "build.txt"

        assert requirement.exists()
