"""Shared fixtures for Conan plugin tests"""

from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest
from packaging.requirements import Requirement
from pytest_mock import MockerFixture

from cppython.plugins.conan.plugin import ConanProvider
from cppython.plugins.conan.schema import ConanDependency

# Shared parameterization for plugin data across all conan tests
CONAN_PLUGIN_DATA_PARAMS = [
    {'remotes': ['conancenter'], 'skip_upload': False},  # Default behavior
    {'remotes': [], 'skip_upload': False},  # Empty remotes (upload to all)
    {'remotes': ['conancenter'], 'skip_upload': True},  # Skip upload with specific remotes
    {'remotes': [], 'skip_upload': True},  # Skip upload with empty remotes
]


@pytest.fixture(name='conan_plugin_data', scope='session', params=CONAN_PLUGIN_DATA_PARAMS)
def fixture_conan_plugin_data(request) -> dict[str, Any]:
    """Shared parameterized plugin data for conan tests

    Returns:
        The constructed plugin data with different combinations of remotes and skip_upload
    """
    return request.param


@pytest.fixture(autouse=True)
def clean_conan_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Sets CONAN_HOME to a temporary directory for each test.

    This ensures all tests run with a clean Conan cache.

    Args:
        tmp_path: Pytest temporary directory fixture
        monkeypatch: Pytest monkeypatch fixture for environment variable manipulation
    """
    conan_home = tmp_path / 'conan_home'
    conan_home.mkdir()

    # Set CONAN_HOME to the temporary directory
    monkeypatch.setenv('CONAN_HOME', str(conan_home))


@pytest.fixture(name='conan_mock_api')
def fixture_conan_mock_api(mocker: MockerFixture) -> Mock:
    """Creates a mock ConanAPI instance for install/update operations

    Args:
        mocker: Pytest mocker fixture

    Returns:
        Mock ConanAPI instance
    """
    mock_api = mocker.Mock()

    # Mock graph module
    mock_deps_graph = mocker.Mock()
    mock_deps_graph.nodes = []
    mock_api.graph.load_graph_consumer = mocker.Mock(return_value=mock_deps_graph)
    mock_api.graph.analyze_binaries = mocker.Mock()

    # Mock install module
    mock_api.install.install_binaries = mocker.Mock()
    mock_api.install.install_consumer = mocker.Mock()

    # Mock remotes module
    mock_remote = mocker.Mock()
    mock_remote.name = 'conancenter'
    mock_api.remotes.list = mocker.Mock(return_value=[mock_remote])

    # Mock profiles module - simulate no default profile by default
    mock_profile = mocker.Mock()
    mock_api.profiles.get_default_host = mocker.Mock(return_value=None)
    mock_api.profiles.get_default_build = mocker.Mock(return_value=None)
    mock_api.profiles.get_profile = mocker.Mock(return_value=mock_profile)
    mock_api.profiles.detect = mocker.Mock(return_value=mock_profile)

    return mock_api


@pytest.fixture(name='conan_mock_api_publish')
def fixture_conan_mock_api_publish(mocker: MockerFixture) -> Mock:
    """Creates a mock ConanAPI instance for publish operations

    Args:
        mocker: Pytest mocker fixture

    Returns:
        Mock ConanAPI instance configured for publish operations
    """
    mock_api = mocker.Mock()

    # Mock export module - export returns a tuple (ref, conanfile)
    mock_ref = mocker.Mock()
    mock_ref.name = 'test_package'
    mock_conanfile = mocker.Mock()
    mock_api.export.export = mocker.Mock(return_value=(mock_ref, mock_conanfile))

    # Mock graph module
    mock_api.graph.load_graph_consumer = mocker.Mock()
    mock_api.graph.analyze_binaries = mocker.Mock()

    # Mock install module
    mock_api.install.install_binaries = mocker.Mock()

    # Mock list module
    mock_select_result = mocker.Mock()
    mock_select_result.recipes = ['some_package/1.0@user/channel']
    mock_api.list.select = mocker.Mock(return_value=mock_select_result)

    # Mock remotes module
    mock_remote = mocker.Mock()
    mock_remote.name = 'conancenter'
    mock_api.remotes.list = mocker.Mock(return_value=[mock_remote])

    # Mock upload module
    mock_api.upload.upload_full = mocker.Mock()

    # Mock profiles module
    mock_profile = mocker.Mock()
    mock_api.profiles.get_default_host = mocker.Mock(return_value='/path/to/default/host')
    mock_api.profiles.get_default_build = mocker.Mock(return_value='/path/to/default/build')
    mock_api.profiles.get_profile = mocker.Mock(return_value=mock_profile)
    mock_api.profiles.detect = mocker.Mock(return_value=mock_profile)

    return mock_api


@pytest.fixture(name='conan_temp_conanfile')
def fixture_conan_temp_conanfile(plugin: ConanProvider) -> Path:
    """Creates a temporary conanfile.py for testing

    Args:
        plugin: The plugin instance

    Returns:
        Path to the created conanfile.py
    """
    project_root = plugin.core_data.project_data.project_root
    conanfile_path = project_root / 'conanfile.py'
    conanfile_path.write_text(
        'from conan import ConanFile\n\nclass TestConan(ConanFile):\n    name = "test_package"\n    version = "1.0"\n'
    )
    return conanfile_path


@pytest.fixture(name='conan_mock_dependencies')
def fixture_conan_mock_dependencies() -> list[Requirement]:
    """Creates mock dependencies for testing

    Returns:
        List of mock requirements
    """
    return [
        Requirement('boost>=1.70.0'),
        Requirement('zlib>=1.2.11'),
    ]


@pytest.fixture(name='conan_setup_mocks')
def fixture_conan_setup_mocks(
    plugin: ConanProvider,
    mocker: MockerFixture,
) -> dict[str, Mock]:
    """Sets up all mocks for testing install/update operations

    Args:
        plugin: The plugin instance
        mocker: Pytest mocker fixture

    Returns:
        Dictionary containing all mocks
    """
    # Mock builder
    mock_builder = mocker.Mock()
    mock_builder.generate_conanfile = mocker.Mock()
    # Set the builder attribute on the plugin
    plugin.builder = mock_builder  # type: ignore[attr-defined]

    # Mock subprocess.run to simulate successful command execution
    mock_subprocess_run = mocker.patch('cppython.plugins.conan.plugin.subprocess.run')
    mock_subprocess_run.return_value = mocker.Mock(returncode=0)

    # Mock resolve_conan_dependency
    def mock_resolve(requirement: Requirement) -> ConanDependency:
        return ConanDependency(name=requirement.name)

    mock_resolve_conan_dependency = mocker.patch(
        'cppython.plugins.conan.plugin.resolve_conan_dependency', side_effect=mock_resolve
    )

    # Mock getLogger to avoid logging setup issues
    mock_logger = mocker.Mock()
    mocker.patch('cppython.plugins.conan.plugin.getLogger', return_value=mock_logger)

    return {
        'builder': mock_builder,
        'subprocess_run': mock_subprocess_run,
        'resolve_conan_dependency': mock_resolve_conan_dependency,
        'logger': mock_logger,
    }
