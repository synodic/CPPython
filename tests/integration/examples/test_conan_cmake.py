"""Integration tests for the conan and CMake project variation.

This module contains integration tests for projects that use conan and CMake.
The tests ensure that the projects build, configure, and execute correctly.
"""

import subprocess
import sys
import tomllib
import zipfile
from pathlib import Path
from tomllib import loads

import pytest
from typer.testing import CliRunner

from cppython.build import build_wheel
from cppython.console.schema import ConsoleInterface
from cppython.core.schema import ProjectConfiguration
from cppython.project import Project

pytest_plugins = ['tests.fixtures.example', 'tests.fixtures.conan', 'tests.fixtures.cmake']

# C++20 modules require Ninja or Visual Studio generator, not Unix Makefiles
_skip_modules_test = pytest.mark.skipif(
    sys.platform != 'win32', reason='C++20 modules require Ninja or Visual Studio generator, not Unix Makefiles.'
)

# On Windows (multi-config generators), use 'default' preset
# On Linux/Mac (single-config generators), use 'default-release' because CMAKE_BUILD_TYPE is required
_cmake_preset = 'default' if sys.platform == 'win32' else 'default-release'


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
    def _run_cmake_configure(cmake_binary: str) -> None:
        """Run CMake configuration and assert success.

        Args:
            cmake_binary: Path or command name for the CMake binary to use
        """
        result = subprocess.run(
            [cmake_binary, f'--preset={_cmake_preset}'], capture_output=True, text=True, check=False
        )
        assert result.returncode == 0, f'CMake configuration failed: {result.stderr}'

    @staticmethod
    def _run_cmake_build(cmake_binary: str) -> None:
        """Run CMake build and assert success.

        Args:
            cmake_binary: Path or command name for the CMake binary to use
        """
        result = subprocess.run([cmake_binary, '--build', 'build'], capture_output=True, text=True, check=False)
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
        # Read cmake_binary from the current pyproject.toml (we're in the example directory)
        pyproject_path = Path.cwd() / 'pyproject.toml'
        with pyproject_path.open('rb') as file:
            pyproject_data = tomllib.load(file)

        cmake_binary = (
            pyproject_data.get('tool', {})
            .get('cppython', {})
            .get('generators', {})
            .get('cmake', {})
            .get('cmake_binary', 'cmake')
        )

        # Create project and install dependencies
        project = TestConanCMake._create_project(skip_upload=False)
        project.install()

        # Configure and verify build
        TestConanCMake._run_cmake_configure(cmake_binary)
        TestConanCMake._verify_build_artifacts()

        # Test publishing with skip_upload enabled
        publish_project = TestConanCMake._create_project(skip_upload=True)
        publish_project.publish()

    @staticmethod
    @_skip_modules_test
    def test_library(example_runner: CliRunner) -> None:
        """Test library creation and packaging workflow"""
        # Read cmake_binary from the current pyproject.toml (we're in the example directory)
        pyproject_path = Path.cwd() / 'pyproject.toml'
        with pyproject_path.open('rb') as file:
            pyproject_data = tomllib.load(file)

        cmake_binary = (
            pyproject_data.get('tool', {})
            .get('cppython', {})
            .get('generators', {})
            .get('cmake', {})
            .get('cmake_binary', 'cmake')
        )

        # Create project and install dependencies
        project = TestConanCMake._create_project(skip_upload=False)
        project.install()

        # Configure, build, and verify
        TestConanCMake._run_cmake_configure(cmake_binary)
        TestConanCMake._run_cmake_build(cmake_binary)
        build_path = TestConanCMake._verify_build_artifacts()

        # Verify library files exist (platform-specific)
        lib_files = list(build_path.glob('**/libmathutils.*')) + list(build_path.glob('**/mathutils.lib'))
        assert len(lib_files) > 0, f'No library files found in {build_path}'

        # Package the library to local cache
        publish_project = TestConanCMake._create_project(skip_upload=True)
        publish_project.publish()

    @staticmethod
    def test_extension(example_runner: CliRunner) -> None:
        """Test Python extension module built with cppython.build backend and scikit-build-core"""
        # This test uses the cppython.build backend which wraps scikit-build-core
        # The build backend automatically runs CPPython's provider workflow

        # Create dist directory for the wheel
        dist_path = Path('dist')
        dist_path.mkdir(exist_ok=True)

        # Build the wheel using the cppython.build backend directly
        wheel_name = build_wheel(str(dist_path))

        # Verify wheel was created
        wheel_path = dist_path / wheel_name
        assert wheel_path.exists(), f'Wheel not created at {wheel_path}'

        # Extract and test the extension
        install_path = Path('install_target')
        install_path.mkdir(exist_ok=True)

        with zipfile.ZipFile(wheel_path, 'r') as whl:
            whl.extractall(install_path)

        # Test the installed extension by adding install_target to path
        test_code = (
            f'import sys; sys.path.insert(0, {str(install_path)!r}); '
            "import example_extension; print(example_extension.format_greeting('Test'))"
        )
        test_result = subprocess.run(
            [sys.executable, '-c', test_code],
            capture_output=True,
            text=True,
            check=False,
        )
        assert test_result.returncode == 0, f'Extension test failed: {test_result.stderr}'
        assert 'Hello, Test!' in test_result.stdout, f'Unexpected output: {test_result.stdout}'
