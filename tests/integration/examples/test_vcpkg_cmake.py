"""Integration tests for the vcpkg and CMake project variation.

This module contains integration tests for projects that use vcpkg and CMake.
The tests ensure that the projects build, configure, and execute correctly.
"""

import subprocess
from pathlib import Path
from tomllib import loads

import pytest
from typer.testing import CliRunner

from cppython.console.schema import ConsoleInterface
from cppython.core.schema import ProjectConfiguration
from cppython.project import Project

pytest_plugins = ['tests.fixtures.example', 'tests.fixtures.vcpkg']


@pytest.mark.skip(reason='Address file locks.')
class TestVcpkgCMake:
    """Test project variation of vcpkg and CMake"""

    @staticmethod
    def _create_project(skip_upload: bool = True) -> Project:
        """Create a project instance with common configuration."""
        project_root = Path.cwd()
        config = ProjectConfiguration(project_root=project_root, version=None, verbosity=2, debug=True)
        interface = ConsoleInterface()

        pyproject_path = project_root / 'pyproject.toml'
        pyproject_data = loads(pyproject_path.read_text(encoding='utf-8'))

        if skip_upload:
            TestVcpkgCMake._ensure_vcpkg_config(pyproject_data)
            pyproject_data['tool']['cppython']['providers']['vcpkg']['skip_upload'] = True

        return Project(config, interface, pyproject_data)

    @staticmethod
    def _ensure_vcpkg_config(pyproject_data: dict) -> None:
        """Helper method to ensure Vcpkg configuration exists in pyproject data"""
        if 'tool' not in pyproject_data:
            pyproject_data['tool'] = {}
        if 'cppython' not in pyproject_data['tool']:
            pyproject_data['tool']['cppython'] = {}
        if 'providers' not in pyproject_data['tool']['cppython']:
            pyproject_data['tool']['cppython']['providers'] = {}
        if 'vcpkg' not in pyproject_data['tool']['cppython']['providers']:
            pyproject_data['tool']['cppython']['providers']['vcpkg'] = {}

    @staticmethod
    def test_simple(example_runner: CliRunner) -> None:
        """Simple project"""
        # Create project and install dependencies
        project = TestVcpkgCMake._create_project(skip_upload=False)
        project.install()

        # Run the CMake configuration command
        result = subprocess.run(['cmake', '--preset=default'], capture_output=True, text=True, check=False)

        assert result.returncode == 0, f'Cmake failed: {result.stderr}'

        # Verify that the build directory contains the expected files
        assert (Path('build') / 'CMakeCache.txt').exists(), 'build/CMakeCache.txt not found'
