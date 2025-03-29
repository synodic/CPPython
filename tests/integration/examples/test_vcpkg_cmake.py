"""TODO"""

from typer.testing import CliRunner

from cppython.console.entry import app

pytest_plugins = ['tests.fixtures.example']


class TestPdmVcpkgCMake:
    """TODO"""

    @staticmethod
    def test_simple(example_runner: CliRunner) -> None:
        """Simple setup of vcpkg and CMake via PDM"""
        result = example_runner.invoke(
            app,
            [
                'update',
            ],
        )

        assert result.exit_code == 0, result.output
