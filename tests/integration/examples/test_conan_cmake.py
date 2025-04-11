"""Integration tests for the conan and CMake project variation.

This module contains integration tests for projects that use conan and CMake.
The tests ensure that the projects build, configure, and execute correctly.
"""

import subprocess
from pathlib import Path

from typer.testing import CliRunner

from cppython.console.entry import app

pytest_plugins = ['tests.fixtures.example']


class TestConanCMake:
    """Test project variation of conan and CMake"""

    @staticmethod
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

        # Verify that the build directory contains the expected files
        assert (Path('build') / 'CMakeCache.txt').exists(), 'build/CMakeCache.txt not found'

    @staticmethod
    def test_inject(example_runner: CliRunner) -> None:
        """Inject"""
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

        # Verify that the build directory contains the expected files
        assert (Path('build') / 'CMakeCache.txt').exists(), 'build/CMakeCache.txt not found'
