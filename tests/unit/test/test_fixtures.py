"""Tests for fixtures"""

from pathlib import Path


class TestFixtures:
    """Tests for fixtures"""

    @staticmethod
    def test_build_directory(build_test_build: Path) -> None:
        """Verifies that the build data provided is the expected path

        Args:
            build_test_build: The plugins build folder directory
        """
        requirement = build_test_build / 'build.txt'

        assert requirement.exists()
