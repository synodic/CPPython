"""Tests the typer interface type"""

from typer.testing import CliRunner

from cppython.console.entry import app

runner = CliRunner()


class TestConsole:
    """Various that all the examples are accessible to cppython. The project should be mocked so nothing executes"""

    @staticmethod
    def test_entrypoint() -> None:
        """Verifies that the entry functions with CPPython hooks"""
        with runner.isolated_filesystem():
            runner.invoke(app, [])
