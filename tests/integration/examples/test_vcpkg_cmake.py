"""TODO"""

from typer.testing import CliRunner

from cppython.console.entry import app

pytest_plugins = ['tests.fixtures.example']


class TestVcpkgCMake:
    """Test project variation of vcpkg and CMake"""

    @staticmethod
    def test_simple(example_runner: CliRunner) -> None:
        """Simple project"""
        result = example_runner.invoke(
            app,
            [
                'update',
            ],
        )

        assert result.exit_code == 0, result.output
