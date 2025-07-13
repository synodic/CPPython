"""Integration tests for the conan and CMake project variation.

This module contains integration tests for projects that use conan and CMake.
The tests ensure that the projects build, configure, and execute correctly.
"""

import subprocess
from pathlib import Path
from tomllib import loads

from typer.testing import CliRunner

from cppython.console.schema import ConsoleInterface
from cppython.core.schema import ProjectConfiguration
from cppython.project import Project

pytest_plugins = ['tests.fixtures.example']


class TestConanCMake:
    """Test project variation of conan and CMake"""

    @staticmethod
    def test_simple(example_runner: CliRunner) -> None:
        """Simple project"""
        # Create project configuration
        project_root = Path.cwd()
        project_configuration = ProjectConfiguration(project_root=project_root, version=None, verbosity=2, debug=True)

        # Create console interface
        interface = ConsoleInterface()

        # Load pyproject.toml data
        pyproject_path = project_root / 'pyproject.toml'
        pyproject_data = loads(pyproject_path.read_text(encoding='utf-8'))

        # Create and use the project directly
        project = Project(project_configuration, interface, pyproject_data)

        # Call install directly to get structured results
        project.install()

        # Run the CMake configuration command
        result = subprocess.run(['cmake', '--preset=default'], capture_output=True, text=True, check=False)

        assert result.returncode == 0, f'Cmake failed: {result.stderr}'

        path = Path('build').absolute()

        # Verify that the build directory contains the expected files
        assert (path / 'CMakeCache.txt').exists(), f'{path / "CMakeCache.txt"} not found'
