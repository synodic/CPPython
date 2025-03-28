"""TODO"""

from typer.testing import CliRunner

pytest_plugins = ['tests.fixtures.example']


class TestPdmVcpkgCMake:
    """TODO"""

    @staticmethod
    def test_simple(example_runner: CliRunner) -> None:
        """Verify that the fixture is returning the right data"""
