"""Integration tests for the vcpkg and CMake project variation.

This module contains integration tests for projects that use vcpkg and CMake.
The tests ensure that the projects build, configure, and execute correctly.
"""

import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

pytest_plugins = ['tests.fixtures.example']


class TestVcpkgCMake:
    """Test project variation of vcpkg and CMake"""

    @staticmethod
    @pytest.mark.skip(reason='TODO')
    def test_simple(example_runner: CliRunner) -> None:
        """Simple project"""
        # By nature of running the test, we require PDM to develop the project and so it will be installed
        result = subprocess.run(['pdm', 'install'], capture_output=True, text=True, check=False)

        assert result.returncode == 0, f'PDM install failed: {result.stderr}'

        # Run the CMake configuration command
        result = subprocess.run(['cmake', '--preset=default'], capture_output=True, text=True, check=False)

        assert result.returncode == 0, f'Cmake failed: {result.stderr}'

        # Verify that the build directory contains the expected files
        assert (Path('build') / 'CMakeCache.txt').exists(), 'build/CMakeCache.txt not found'
