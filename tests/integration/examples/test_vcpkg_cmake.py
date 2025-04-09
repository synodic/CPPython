"""TODO"""

import subprocess

import pytest
from typer.testing import CliRunner

from cppython.console.entry import app

pytest_plugins = ['tests.fixtures.example']


class TestVcpkgCMake:
    """Test project variation of vcpkg and CMake"""

    @staticmethod
    @pytest.mark.skip(reason='TODO')
    def test_simple(example_runner: CliRunner) -> None:
        """Simple project"""
        result = example_runner.invoke(
            app,
            [
                'install',
            ],
        )

        assert result.exit_code == 0, result.output

        # Run the CMake configuration command
        cmake_result = subprocess.run(['cmake', '--preset=default'], capture_output=True, text=True, check=False)

        assert cmake_result.returncode == 0, f'CMake configuration failed: {cmake_result.stderr}'

        # Run the CMake build command
        build_result = subprocess.run(['cmake', '--build', 'build'], capture_output=True, text=True, check=False)

        assert build_result.returncode == 0, f'CMake build failed: {build_result.stderr}'
        assert 'Build finished successfully' in build_result.stdout, 'CMake build did not finish successfully'

        # Execute the built program and verify the output
        program_result = subprocess.run(['build/HelloWorld'], capture_output=True, text=True, check=False)

        assert program_result.returncode == 0, f'Program execution failed: {program_result.stderr}'

        assert 'Hello, World!' in program_result.stdout, 'Program output did not match expected output'
