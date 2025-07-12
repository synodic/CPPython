"""Unit tests for the conan plugin publish functionality"""

from typing import Any
from unittest.mock import MagicMock, Mock

import pytest
from pytest_mock import MockerFixture

from cppython.plugins.conan.plugin import ConanProvider
from cppython.test.pytest.mixins import ProviderPluginTestMixin


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
            'local': False,
        }

    @staticmethod
    @pytest.fixture(name='plugin_type', scope='session')
    def fixture_plugin_type() -> type[ConanProvider]:
        """A required testing hook that allows type generation

        Returns:
            The type of the Provider
        """
        return ConanProvider

    @staticmethod
    @pytest.fixture(name='mock_conan_api')
    def fixture_mock_conan_api(mocker: MockerFixture) -> Mock:
        """Creates a mock ConanAPI instance

        Args:
            mocker: Pytest mocker fixture

        Returns:
            Mock ConanAPI instance
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
        mock_remote.name = 'origin'
        mock_api.remotes.list = mocker.Mock(return_value=[mock_remote])

        # Mock upload module
        mock_api.upload.upload_full = mocker.Mock()

        # Mock profiles module
        mock_profile = mocker.Mock()
        mock_api.profiles.get_profiles_from_args = mocker.Mock(return_value=(mock_profile, mock_profile))

        return mock_api

    @staticmethod
    @pytest.fixture(name='temp_conanfile')
    def fixture_temp_conanfile(plugin: ConanProvider) -> None:
        """Creates a temporary conanfile.py for testing

        Args:
            plugin: The plugin instance
        """
        project_root = plugin.core_data.project_data.project_root
        conanfile_path = project_root / 'conanfile.py'
        conanfile_path.write_text(
            'from conan import ConanFile\n\n'
            'class TestConan(ConanFile):\n'
            '    name = "test_package"\n'
            '    version = "1.0"\n'
        )

    def test_publish_local_only(
        self, plugin: ConanProvider, mock_conan_api: Mock, temp_conanfile: None, mocker: MockerFixture
    ) -> None:
        """Test that publish with local=True only exports and builds locally

        Args:
            plugin: The plugin instance
            mock_conan_api: Mock ConanAPI
            temp_conanfile: Fixture to create conanfile.py
            mocker: Pytest mocker fixture
        """
        # Set plugin to local mode
        plugin.data.local = True

        # Mock the necessary imports and API creation
        mocker.patch('cppython.plugins.conan.plugin.ConanAPI', return_value=mock_conan_api)

        # Mock the dependencies graph
        mock_graph = mocker.Mock()
        mock_conan_api.graph.load_graph_consumer.return_value = mock_graph

        # Execute publish
        plugin.publish()

        # Verify export was called
        mock_conan_api.export.export.assert_called_once()

        # Verify graph loading and analysis
        mock_conan_api.graph.load_graph_consumer.assert_called_once()
        mock_conan_api.graph.analyze_binaries.assert_called_once_with(
            graph=mock_graph,
            build_mode=['*'],
            remotes=mock_conan_api.remotes.list(),
            update=None,
            lockfile=None,
        )

        # Verify install was called
        mock_conan_api.install.install_binaries.assert_called_once_with(
            deps_graph=mock_graph, remotes=mock_conan_api.remotes.list()
        )

        # Verify upload was NOT called for local mode
        mock_conan_api.upload.upload_full.assert_not_called()

    def test_publish_with_upload(
        self, plugin: ConanProvider, mock_conan_api: Mock, temp_conanfile: None, mocker: MockerFixture
    ) -> None:
        """Test that publish with local=False exports, builds, and uploads

        Args:
            plugin: The plugin instance
            mock_conan_api: Mock ConanAPI
            temp_conanfile: Fixture to create conanfile.py
            mocker: Pytest mocker fixture
        """
        # Set plugin to upload mode
        plugin.data.local = False

        # Mock the necessary imports and API creation
        mocker.patch('cppython.plugins.conan.plugin.ConanAPI', return_value=mock_conan_api)

        # Mock the dependencies graph
        mock_graph = mocker.Mock()
        mock_conan_api.graph.load_graph_consumer.return_value = mock_graph

        # Execute publish
        plugin.publish()

        # Verify all steps were called
        mock_conan_api.export.export.assert_called_once()
        mock_conan_api.graph.load_graph_consumer.assert_called_once()
        mock_conan_api.graph.analyze_binaries.assert_called_once()
        mock_conan_api.install.install_binaries.assert_called_once()

        # Verify upload was called
        mock_conan_api.list.select.assert_called_once()
        mock_conan_api.upload.upload_full.assert_called_once()

    def test_publish_no_remotes_configured(
        self, plugin: ConanProvider, mock_conan_api: Mock, temp_conanfile: None, mocker: MockerFixture
    ) -> None:
        """Test that publish raises error when no remotes are configured for upload

        Args:
            plugin: The plugin instance
            mock_conan_api: Mock ConanAPI
            temp_conanfile: Fixture to create conanfile.py
            mocker: Pytest mocker fixture
        """
        # Set plugin to upload mode
        plugin.data.local = False

        # Mock the necessary imports and API creation
        mocker.patch('cppython.plugins.conan.plugin.ConanAPI', return_value=mock_conan_api)

        # Mock the dependencies graph
        mock_graph = mocker.Mock()
        mock_conan_api.graph.load_graph_consumer.return_value = mock_graph

        # Mock no remotes configured
        mock_conan_api.remotes.list.return_value = []

        # Execute publish and expect RuntimeError
        with pytest.raises(RuntimeError, match='No remotes configured for upload'):
            plugin.publish()

    def test_publish_no_packages_found(
        self, plugin: ConanProvider, mock_conan_api: Mock, temp_conanfile: None, mocker: MockerFixture
    ) -> None:
        """Test that publish raises error when no packages are found to upload

        Args:
            plugin: The plugin instance
            mock_conan_api: Mock ConanAPI
            temp_conanfile: Fixture to create conanfile.py
            mocker: Pytest mocker fixture
        """
        # Set plugin to upload mode
        plugin.data.local = False

        # Mock the necessary imports and API creation
        mocker.patch('cppython.plugins.conan.plugin.ConanAPI', return_value=mock_conan_api)

        # Mock the dependencies graph
        mock_graph = mocker.Mock()
        mock_conan_api.graph.load_graph_consumer.return_value = mock_graph

        # Mock empty package list
        mock_select_result = mocker.Mock()
        mock_select_result.recipes = []
        mock_conan_api.list.select.return_value = mock_select_result

        # Execute publish and expect RuntimeError
        with pytest.raises(RuntimeError, match='No packages found to upload'):
            plugin.publish()

    def test_publish_uses_default_profiles(
        self, plugin: ConanProvider, mock_conan_api: Mock, temp_conanfile: None, mocker: MockerFixture
    ) -> None:
        """Test that publish uses default profiles from API

        Args:
            plugin: The plugin instance
            mock_conan_api: Mock ConanAPI
            temp_conanfile: Fixture to create conanfile.py
            mocker: Pytest mocker fixture
        """
        # Set plugin to local mode
        plugin.data.local = True

        # Mock the necessary imports and API creation
        mocker.patch('cppython.plugins.conan.plugin.ConanAPI', return_value=mock_conan_api)

        # Mock the dependencies graph
        mock_graph = mocker.Mock()
        mock_conan_api.graph.load_graph_consumer.return_value = mock_graph

        # Execute publish
        plugin.publish()

        # Verify profiles were obtained from API
        mock_conan_api.profiles.get_profiles_from_args.assert_called_once_with([])

    def test_publish_upload_parameters(
        self, plugin: ConanProvider, mock_conan_api: Mock, temp_conanfile: None, mocker: MockerFixture
    ) -> None:
        """Test that publish upload is called with correct parameters

        Args:
            plugin: The plugin instance
            mock_conan_api: Mock ConanAPI
            temp_conanfile: Fixture to create conanfile.py
            mocker: Pytest mocker fixture
        """
        # Set plugin to upload mode
        plugin.data.local = False

        # Mock the necessary imports and API creation
        mocker.patch('cppython.plugins.conan.plugin.ConanAPI', return_value=mock_conan_api)

        # Mock the dependencies graph
        mock_graph = mocker.Mock()
        mock_conan_api.graph.load_graph_consumer.return_value = mock_graph

        # Mock remotes and package list
        mock_remote = MagicMock()
        mock_remote.name = 'origin'
        remotes = [mock_remote]
        mock_conan_api.remotes.list.return_value = remotes

        mock_package_list = MagicMock()
        mock_package_list.recipes = ['test_package/1.0@user/channel']
        mock_conan_api.list.select.return_value = mock_package_list

        # Execute publish
        plugin.publish()

        # Verify upload_full was called with correct parameters
        mock_conan_api.upload.upload_full.assert_called_once_with(
            package_list=mock_package_list,
            remote=mock_remote,
            enabled_remotes=remotes,
            check_integrity=False,
            force=False,
            metadata=None,
            dry_run=False,
        )

    def test_publish_list_pattern_creation(
        self, plugin: ConanProvider, mock_conan_api: Mock, temp_conanfile: None, mocker: MockerFixture
    ) -> None:
        """Test that publish creates correct ListPattern for package selection

        Args:
            plugin: The plugin instance
            mock_conan_api: Mock ConanAPI
            temp_conanfile: Fixture to create conanfile.py
            mocker: Pytest mocker fixture
        """
        # Set plugin to upload mode
        plugin.data.local = False

        # Mock the necessary imports and API creation
        mocker.patch('cppython.plugins.conan.plugin.ConanAPI', return_value=mock_conan_api)
        mock_list_pattern = mocker.patch('cppython.plugins.conan.plugin.ListPattern')

        # Mock the dependencies graph
        mock_graph = mocker.Mock()
        mock_conan_api.graph.load_graph_consumer.return_value = mock_graph

        # Execute publish
        plugin.publish()

        # Get the ref from the export call to verify ListPattern creation
        # The export call returns (ref, conanfile) - we need the ref.name
        export_return = mock_conan_api.export.export.return_value
        ref = export_return[0]  # First element of the tuple

        # Verify ListPattern was created with correct reference pattern
        mock_list_pattern.assert_called_once_with(f'{ref.name}/*', package_id='*', only_recipe=False)
