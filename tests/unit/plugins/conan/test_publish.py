"""Unit tests for the conan plugin publish functionality"""

from typing import Any
from unittest.mock import MagicMock, Mock

import pytest
from pytest_mock import MockerFixture

from cppython.plugins.conan.plugin import ConanProvider
from cppython.test.pytest.mixins import ProviderPluginTestMixin
from cppython.utility.exception import ProviderConfigurationError, ProviderInstallationError

# Use shared fixtures
pytest_plugins = ['tests.fixtures.conan']

# Constants for test assertions
EXPECTED_PROFILE_CALLS = 2


class TestConanPublish(ProviderPluginTestMixin[ConanProvider]):
    """Tests for the Conan provider publish functionality"""

    @staticmethod
    @pytest.fixture(name='plugin_data', scope='session')
    def fixture_plugin_data() -> dict[str, Any]:
        """A required testing hook that allows data generation

        Returns:
            The constructed plugin data
        """
        return {
            'remotes': ['conancenter'],
        }

    @staticmethod
    @pytest.fixture(name='plugin_type', scope='session')
    def fixture_plugin_type() -> type[ConanProvider]:
        """A required testing hook that allows type generation

        Returns:
            The type of the Provider
        """
        return ConanProvider

    def test_publish_local_only(
        self, plugin: ConanProvider, conan_mock_api_publish: Mock, conan_temp_conanfile: None, mocker: MockerFixture
    ) -> None:
        """Test that publish with remotes=[] only exports and builds locally

        Args:
            plugin: The plugin instance
            conan_mock_api_publish: Mock ConanAPI for publish operations
            conan_temp_conanfile: Fixture to create conanfile.py
            mocker: Pytest mocker fixture
        """
        # Set plugin to local mode
        plugin.data.remotes = []

        # Mock the necessary imports and API creation
        mocker.patch('cppython.plugins.conan.plugin.ConanAPI', return_value=conan_mock_api_publish)

        # Mock the dependencies graph
        mock_graph = mocker.Mock()
        conan_mock_api_publish.graph.load_graph_consumer.return_value = mock_graph

        # Execute publish
        plugin.publish()

        # Verify export was called
        conan_mock_api_publish.export.export.assert_called_once()

        # Verify graph loading and analysis
        conan_mock_api_publish.graph.load_graph_consumer.assert_called_once()
        conan_mock_api_publish.graph.analyze_binaries.assert_called_once_with(
            graph=mock_graph,
            build_mode=['*'],
            remotes=conan_mock_api_publish.remotes.list(),
            update=None,
            lockfile=None,
        )

        # Verify install was called
        conan_mock_api_publish.install.install_binaries.assert_called_once_with(
            deps_graph=mock_graph, remotes=conan_mock_api_publish.remotes.list()
        )

        # Verify upload was NOT called for local mode
        conan_mock_api_publish.upload.upload_full.assert_not_called()

    def test_publish_with_upload(
        self, plugin: ConanProvider, conan_mock_api_publish: Mock, conan_temp_conanfile: None, mocker: MockerFixture
    ) -> None:
        """Test that publish with remotes=['conancenter'] exports, builds, and uploads

        Args:
            plugin: The plugin instance
            conan_mock_api_publish: Mock ConanAPI for publish operations
            conan_temp_conanfile: Fixture to create conanfile.py
            mocker: Pytest mocker fixture
        """
        # Set plugin to upload mode
        plugin.data.remotes = ['conancenter']

        # Mock the necessary imports and API creation
        mocker.patch('cppython.plugins.conan.plugin.ConanAPI', return_value=conan_mock_api_publish)

        # Mock the dependencies graph
        mock_graph = mocker.Mock()
        conan_mock_api_publish.graph.load_graph_consumer.return_value = mock_graph

        # Execute publish
        plugin.publish()

        # Verify all steps were called
        conan_mock_api_publish.export.export.assert_called_once()
        conan_mock_api_publish.graph.load_graph_consumer.assert_called_once()
        conan_mock_api_publish.graph.analyze_binaries.assert_called_once()
        conan_mock_api_publish.install.install_binaries.assert_called_once()

        # Verify upload was called
        conan_mock_api_publish.list.select.assert_called_once()
        conan_mock_api_publish.upload.upload_full.assert_called_once()

    def test_publish_no_remotes_configured(
        self, plugin: ConanProvider, conan_mock_api_publish: Mock, conan_temp_conanfile: None, mocker: MockerFixture
    ) -> None:
        """Test that publish raises error when no remotes are configured for upload

        Args:
            plugin: The plugin instance
            conan_mock_api_publish: Mock ConanAPI for publish operations
            conan_temp_conanfile: Fixture to create conanfile.py
            mocker: Pytest mocker fixture
        """
        # Set plugin to upload mode
        plugin.data.remotes = ['conancenter']

        # Mock the necessary imports and API creation
        mocker.patch('cppython.plugins.conan.plugin.ConanAPI', return_value=conan_mock_api_publish)

        # Mock the dependencies graph
        mock_graph = mocker.Mock()
        conan_mock_api_publish.graph.load_graph_consumer.return_value = mock_graph

        # Mock no remotes configured
        conan_mock_api_publish.remotes.list.return_value = []

        # Execute publish and expect ProviderConfigurationError
        with pytest.raises(ProviderConfigurationError, match='No configured remotes found'):
            plugin.publish()

    def test_publish_no_packages_found(
        self, plugin: ConanProvider, conan_mock_api_publish: Mock, conan_temp_conanfile: None, mocker: MockerFixture
    ) -> None:
        """Test that publish raises error when no packages are found to upload

        Args:
            plugin: The plugin instance
            conan_mock_api_publish: Mock ConanAPI for publish operations
            conan_temp_conanfile: Fixture to create conanfile.py
            mocker: Pytest mocker fixture
        """
        # Set plugin to upload mode
        plugin.data.remotes = ['conancenter']

        # Mock the necessary imports and API creation
        mocker.patch('cppython.plugins.conan.plugin.ConanAPI', return_value=conan_mock_api_publish)

        # Mock the dependencies graph
        mock_graph = mocker.Mock()
        conan_mock_api_publish.graph.load_graph_consumer.return_value = mock_graph

        # Mock empty package list
        mock_select_result = mocker.Mock()
        mock_select_result.recipes = []
        conan_mock_api_publish.list.select.return_value = mock_select_result

        # Execute publish and expect ProviderInstallationError
        with pytest.raises(ProviderInstallationError, match='No packages found to upload'):
            plugin.publish()

    def test_publish_uses_default_profiles(
        self, plugin: ConanProvider, conan_mock_api_publish: Mock, conan_temp_conanfile: None, mocker: MockerFixture
    ) -> None:
        """Test that publish uses default profiles from API

        Args:
            plugin: The plugin instance
            conan_mock_api_publish: Mock ConanAPI for publish operations
            conan_temp_conanfile: Fixture to create conanfile.py
            mocker: Pytest mocker fixture
        """
        # Set plugin to local mode
        plugin.data.remotes = []

        # Mock the necessary imports and API creation
        mocker.patch('cppython.plugins.conan.plugin.ConanAPI', return_value=conan_mock_api_publish)

        # Mock the dependencies graph
        mock_graph = mocker.Mock()
        conan_mock_api_publish.graph.load_graph_consumer.return_value = mock_graph

        # Execute publish
        plugin.publish()

        # Verify profiles were obtained from API
        conan_mock_api_publish.profiles.get_default_host.assert_called_once()
        conan_mock_api_publish.profiles.get_default_build.assert_called_once()
        conan_mock_api_publish.profiles.get_profile.assert_called()

    def test_publish_upload_parameters(
        self, plugin: ConanProvider, conan_mock_api_publish: Mock, conan_temp_conanfile: None, mocker: MockerFixture
    ) -> None:
        """Test that publish upload is called with correct parameters

        Args:
            plugin: The plugin instance
            conan_mock_api_publish: Mock ConanAPI for publish operations
            conan_temp_conanfile: Fixture to create conanfile.py
            mocker: Pytest mocker fixture
        """
        # Set plugin to upload mode
        plugin.data.remotes = ['conancenter']

        # Mock the necessary imports and API creation
        mocker.patch('cppython.plugins.conan.plugin.ConanAPI', return_value=conan_mock_api_publish)

        # Mock the dependencies graph
        mock_graph = mocker.Mock()
        conan_mock_api_publish.graph.load_graph_consumer.return_value = mock_graph

        # Mock remotes and package list
        mock_remote = MagicMock()
        mock_remote.name = 'conancenter'
        remotes = [mock_remote]
        conan_mock_api_publish.remotes.list.return_value = remotes

        mock_package_list = MagicMock()
        mock_package_list.recipes = ['test_package/1.0@user/channel']
        conan_mock_api_publish.list.select.return_value = mock_package_list

        # Execute publish
        plugin.publish()

        # Verify upload_full was called with correct parameters
        conan_mock_api_publish.upload.upload_full.assert_called_once_with(
            package_list=mock_package_list,
            remote=mock_remote,
            enabled_remotes=remotes,
            check_integrity=False,
            force=False,
            metadata=None,
            dry_run=False,
        )

    def test_publish_list_pattern_creation(
        self, plugin: ConanProvider, conan_mock_api_publish: Mock, conan_temp_conanfile: None, mocker: MockerFixture
    ) -> None:
        """Test that publish creates correct ListPattern for package selection

        Args:
            plugin: The plugin instance
            conan_mock_api_publish: Mock ConanAPI for publish operations
            conan_temp_conanfile: Fixture to create conanfile.py
            mocker: Pytest mocker fixture
        """
        # Set plugin to upload mode
        plugin.data.remotes = ['conancenter']

        # Mock the necessary imports and API creation
        mocker.patch('cppython.plugins.conan.plugin.ConanAPI', return_value=conan_mock_api_publish)
        mock_list_pattern = mocker.patch('cppython.plugins.conan.plugin.ListPattern')

        # Mock the dependencies graph
        mock_graph = mocker.Mock()
        conan_mock_api_publish.graph.load_graph_consumer.return_value = mock_graph

        # Execute publish
        plugin.publish()

        # Get the ref from the export call to verify ListPattern creation
        # The export call returns (ref, conanfile) - we need the ref.name
        export_return = conan_mock_api_publish.export.export.return_value
        ref = export_return[0]  # First element of the tuple

        # Verify ListPattern was created with correct reference pattern
        mock_list_pattern.assert_called_once_with(f'{ref.name}/*', package_id='*', only_recipe=False)
