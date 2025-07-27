"""Integration tests for the conan and CMake project variation.

This module contains integration tests for projects that use conan and CMake.
The tests ensure that the projects build, configure, and execute correctly.
"""

import os
import shutil
import subprocess
from pathlib import Path
from tomllib import loads

from typer.testing import CliRunner

from cppython.console.schema import ConsoleInterface
from cppython.core.schema import ProjectConfiguration
from cppython.project import Project

pytest_plugins = ['tests.fixtures.example', 'tests.fixtures.conan']


class TestConanCMake:
    """Test project variation of conan and CMake"""

    @staticmethod
    def _create_project(skip_upload: bool = True) -> Project:
        """Create a project instance with common configuration."""
        project_root = Path.cwd()
        config = ProjectConfiguration(project_root=project_root, version=None, verbosity=2, debug=True)
        interface = ConsoleInterface()

        pyproject_path = project_root / 'pyproject.toml'
        pyproject_data = loads(pyproject_path.read_text(encoding='utf-8'))

        if skip_upload:
            TestConanCMake._ensure_conan_config(pyproject_data)
            pyproject_data['tool']['cppython']['providers']['conan']['skip_upload'] = True

        return Project(config, interface, pyproject_data)

    @staticmethod
    def _run_cmake_configure() -> None:
        """Run CMake configuration and assert success."""
        result = subprocess.run(['cmake', '--preset=default'], capture_output=True, text=True, check=False)
        assert result.returncode == 0, f'CMake configuration failed: {result.stderr}'

    @staticmethod
    def _run_cmake_build() -> None:
        """Run CMake build and assert success."""
        result = subprocess.run(['cmake', '--build', 'build'], capture_output=True, text=True, check=False)
        assert result.returncode == 0, f'CMake build failed: {result.stderr}'

    @staticmethod
    def _verify_build_artifacts() -> Path:
        """Verify basic build artifacts exist and return build path."""
        build_path = Path('build').absolute()
        assert (build_path / 'CMakeCache.txt').exists(), f'CMakeCache.txt not found in {build_path}'
        return build_path

    @staticmethod
    def _ensure_conan_config(pyproject_data: dict) -> None:
        """Helper method to ensure Conan configuration exists in pyproject data"""
        if 'tool' not in pyproject_data:
            pyproject_data['tool'] = {}
        if 'cppython' not in pyproject_data['tool']:
            pyproject_data['tool']['cppython'] = {}
        if 'providers' not in pyproject_data['tool']['cppython']:
            pyproject_data['tool']['cppython']['providers'] = {}
        if 'conan' not in pyproject_data['tool']['cppython']['providers']:
            pyproject_data['tool']['cppython']['providers']['conan'] = {}

    @staticmethod
    def test_simple(example_runner: CliRunner) -> None:
        """Simple project"""
        # Create project and install dependencies
        project = TestConanCMake._create_project(skip_upload=False)
        project.install()

        # Configure and verify build
        TestConanCMake._run_cmake_configure()
        TestConanCMake._verify_build_artifacts()

        # Test publishing with skip_upload enabled
        publish_project = TestConanCMake._create_project(skip_upload=True)
        publish_project.publish()

    @staticmethod
    def test_library(example_runner: CliRunner) -> None:
        """Test library creation and packaging workflow"""
        # Create project and install dependencies
        project = TestConanCMake._create_project(skip_upload=False)
        project.install()

        # Configure, build, and verify
        TestConanCMake._run_cmake_configure()
        TestConanCMake._run_cmake_build()
        build_path = TestConanCMake._verify_build_artifacts()

        # Verify library files exist (platform-specific)
        lib_files = list(build_path.glob('**/libmathutils.*')) + list(build_path.glob('**/mathutils.lib'))
        assert len(lib_files) > 0, f'No library files found in {build_path}'

        # Package the library to local cache
        publish_project = TestConanCMake._create_project(skip_upload=True)
        publish_project.publish()

    @staticmethod
    def _publish_library_to_cache() -> None:
        """Helper method to publish the library to local Conan cache"""
        examples_root = Path(__file__).parent.parent.parent.parent / 'examples'
        library_source = examples_root / 'conan_cmake' / 'library'
        library_temp = Path('temp_library')

        # Clean up any existing temp directory first
        if library_temp.exists():
            shutil.rmtree(library_temp)

        # Copy library to temp location
        shutil.copytree(library_source, library_temp)

        # Change to library directory and publish it
        original_cwd = Path.cwd()
        try:
            os.chdir(library_temp)

            # Create and configure library project
            lib_project = TestConanCMake._create_project(skip_upload=True)
            lib_project.install()

            # Build and publish library
            TestConanCMake._run_cmake_configure()
            TestConanCMake._run_cmake_build()
            lib_project.publish()

        finally:
            os.chdir(original_cwd)
            # Clean up temp directory
            if library_temp.exists():
                shutil.rmtree(library_temp)

    @staticmethod
    def test_library_consumer(example_runner: CliRunner) -> None:
        """Test that a consumer can use the published library"""
        # First, publish the library to the local cache
        TestConanCMake._publish_library_to_cache()

        # Create consumer project and install dependencies
        consumer_project = TestConanCMake._create_project(skip_upload=False)
        consumer_project.install()

        # Configure and build the consumer
        TestConanCMake._run_cmake_configure()
        TestConanCMake._run_cmake_build()
        build_path = TestConanCMake._verify_build_artifacts()

        # Verify the executable was created and works
        exe_files = list(build_path.glob('**/consumer*'))
        assert len(exe_files) > 0, f'No consumer executable found in {build_path}'

        # Run the consumer to verify it works
        exe_path = next((f for f in exe_files if f.suffix == '.exe' or f.is_file()), None)
        if exe_path:
            result = subprocess.run([str(exe_path)], capture_output=True, text=True, check=False)
            assert result.returncode == 0, f'Consumer execution failed: {result.stderr}'
            assert 'MathUtils' in result.stdout, f'Expected MathUtils output not found: {result.stdout}'
