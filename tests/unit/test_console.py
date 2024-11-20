"""Tests the typer interface type"""

from typer.testing import CliRunner

from cppython.console.entry import app

runner = CliRunner()


class TestConsole:
    """Various tests for the typer interface"""

    def test_info(self) -> None:
        """Verifies that the info command functions with CPPython hooks"""
        result = runner.invoke(app, ['info'])
        assert result.exit_code == 0

    def test_list(self) -> None:
        """Verifies that the list command functions with CPPython hooks"""
        result = runner.invoke(app, ['list'])
        assert result.exit_code == 0

    def test_update(self) -> None:
        """Verifies that the update command functions with CPPython hooks"""
        result = runner.invoke(app, ['update'])
        assert result.exit_code == 0

    def test_install(self) -> None:
        """Verifies that the install command functions with CPPython hooks"""
        result = runner.invoke(app, ['install'])
        assert result.exit_code == 0
