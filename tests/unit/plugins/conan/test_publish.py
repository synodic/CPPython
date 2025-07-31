"""Unit tests for the conan plugin publish functionality"""

import subprocess
from typing import Any

import pytest
from pytest_mock import MockerFixture

from cppython.plugins.conan.plugin import ConanProvider
from cppython.test.pytest.mixins import ProviderPluginTestMixin
from cppython.utility.exception import ProviderInstallationError

# Use shared fixtures
pytest_plugins = ['tests.fixtures.conan']

# Constants for test assertions
EXPECTED_SUBPROCESS_CALLS_WITH_UPLOAD = 2
EXPECTED_SUBPROCESS_CALLS_SINGLE = 1


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

    def test_skip_upload(
        self, plugin: ConanProvider, conan_temp_conanfile: None, mocker: MockerFixture
    ) -> None:
        """Test that publish with skip_upload=True only runs conan create without upload

        Args:
            plugin: The plugin instance
            conan_temp_conanfile: Fixture to create conanfile.py
            mocker: Pytest mocker fixture
        """
        # Set plugin to skip upload mode
        plugin.data.skip_upload = True

        # Mock subprocess.run
        mock_subprocess_run = mocker.patch('cppython.plugins.conan.plugin.subprocess.run')
        mock_subprocess_run.return_value = mocker.Mock(returncode=0)

        # Mock getLogger
        mock_logger = mocker.Mock()
        mocker.patch('cppython.plugins.conan.plugin.getLogger', return_value=mock_logger)

        # Execute publish
        plugin.publish()

        # Verify subprocess.run was called once for conan create
        mock_subprocess_run.assert_called_once()
        call_args = mock_subprocess_run.call_args[0][0]
        assert call_args[0] == 'conan'
        assert call_args[1] == 'create'
        assert '--build' in call_args
        assert 'missing' in call_args

        # Verify no upload commands were executed (since skip_upload=True)
        assert mock_subprocess_run.call_count == EXPECTED_SUBPROCESS_CALLS_SINGLE

    def test_with_upload(
        self, plugin: ConanProvider, conan_temp_conanfile: None, mocker: MockerFixture
    ) -> None:
        """Test that publish with remotes=['conancenter'] runs conan create and upload

        Args:
            plugin: The plugin instance
            conan_temp_conanfile: Fixture to create conanfile.py
            mocker: Pytest mocker fixture
        """
        # Set plugin to upload mode
        plugin.data.remotes = ['conancenter']
        plugin.data.skip_upload = False

        # Mock subprocess.run
        mock_subprocess_run = mocker.patch('cppython.plugins.conan.plugin.subprocess.run')
        mock_subprocess_run.return_value = mocker.Mock(returncode=0)

        # Mock getLogger
        mock_logger = mocker.Mock()
        mocker.patch('cppython.plugins.conan.plugin.getLogger', return_value=mock_logger)

        # Execute publish
        plugin.publish()

        # Verify subprocess.run was called twice (create + upload)
        assert mock_subprocess_run.call_count == EXPECTED_SUBPROCESS_CALLS_WITH_UPLOAD

        # Check first call - conan create
        create_call_args = mock_subprocess_run.call_args_list[0][0][0]
        assert create_call_args[0] == 'conan'
        assert create_call_args[1] == 'create'

        # Check second call - conan upload
        upload_call_args = mock_subprocess_run.call_args_list[1][0][0]
        assert upload_call_args[0] == 'conan'
        assert upload_call_args[1] == 'upload'
        assert '--remote' in upload_call_args
        assert 'conancenter' in upload_call_args

    def test_upload_to_all_remotes(
        self, plugin: ConanProvider, conan_temp_conanfile: None, mocker: MockerFixture
    ) -> None:
        """Test that publish with empty remotes list uploads to all available remotes

        Args:
            plugin: The plugin instance
            conan_temp_conanfile: Fixture to create conanfile.py
            mocker: Pytest mocker fixture
        """
        # Set plugin to upload to all remotes
        plugin.data.remotes = []
        plugin.data.skip_upload = False

        # Mock subprocess.run
        mock_subprocess_run = mocker.patch('cppython.plugins.conan.plugin.subprocess.run')
        mock_subprocess_run.return_value = mocker.Mock(returncode=0)

        # Mock getLogger
        mock_logger = mocker.Mock()
        mocker.patch('cppython.plugins.conan.plugin.getLogger', return_value=mock_logger)

        # Execute publish
        plugin.publish()

        # Verify subprocess.run was called twice (create + upload)
        assert mock_subprocess_run.call_count == EXPECTED_SUBPROCESS_CALLS_WITH_UPLOAD

        # Check second call - conan upload to all remotes
        upload_call_args = mock_subprocess_run.call_args_list[1][0][0]
        assert upload_call_args[0] == 'conan'
        assert upload_call_args[1] == 'upload'
        assert '--all' in upload_call_args
        assert '--confirm' in upload_call_args

    def test_conan_create_failure(
        self, plugin: ConanProvider, conan_temp_conanfile: None, mocker: MockerFixture
    ) -> None:
        """Test that publish raises error when conan create fails

        Args:
            plugin: The plugin instance
            conan_temp_conanfile: Fixture to create conanfile.py
            mocker: Pytest mocker fixture
        """
        # Set plugin to skip upload mode for simpler test
        plugin.data.skip_upload = True

        # Mock subprocess.run to fail
        mock_subprocess_run = mocker.patch('cppython.plugins.conan.plugin.subprocess.run')
        mock_subprocess_run.side_effect = subprocess.CalledProcessError(
            1, ['conan', 'create'], stderr='Conan create failed: missing dependency'
        )

        # Mock getLogger
        mock_logger = mocker.Mock()
        mocker.patch('cppython.plugins.conan.plugin.getLogger', return_value=mock_logger)

        # Execute publish and expect ProviderInstallationError
        with pytest.raises(ProviderInstallationError, match='Conan create failed: missing dependency'):
            plugin.publish()

    def test_conan_upload_failure(
        self, plugin: ConanProvider, conan_temp_conanfile: None, mocker: MockerFixture
    ) -> None:
        """Test that publish raises error when conan upload fails

        Args:
            plugin: The plugin instance
            conan_temp_conanfile: Fixture to create conanfile.py
            mocker: Pytest mocker fixture
        """
        # Set plugin to upload mode
        plugin.data.remotes = ['conancenter']
        plugin.data.skip_upload = False

        # Mock subprocess.run
        mock_subprocess_run = mocker.patch('cppython.plugins.conan.plugin.subprocess.run')
        
        # First call (create) succeeds, second call (upload) fails
        def subprocess_side_effect(*args, **kwargs):
            if 'create' in args[0]:
                return mocker.Mock(returncode=0)
            elif 'upload' in args[0]:
                raise subprocess.CalledProcessError(
                    1, ['conan', 'upload'], stderr='Upload failed: authentication error'
                )
            
        mock_subprocess_run.side_effect = subprocess_side_effect

        # Mock getLogger
        mock_logger = mocker.Mock()
        mocker.patch('cppython.plugins.conan.plugin.getLogger', return_value=mock_logger)

        # Execute publish and expect ProviderInstallationError
        with pytest.raises(ProviderInstallationError, match='Upload to conancenter failed'):
            plugin.publish()

    def test_with_custom_profiles(
        self, plugin: ConanProvider, conan_temp_conanfile: None, mocker: MockerFixture
    ) -> None:
        """Test that publish uses custom profiles when specified

        Args:
            plugin: The plugin instance
            conan_temp_conanfile: Fixture to create conanfile.py
            mocker: Pytest mocker fixture
        """
        # Set plugin to skip upload mode for simpler test
        plugin.data.skip_upload = True

        # Mock custom profiles
        custom_host_profile = mocker.Mock()
        custom_build_profile = mocker.Mock()
        
        # Override profiles in the plugin data
        plugin.data.host_profile = custom_host_profile
        plugin.data.build_profile = custom_build_profile

        # Mock subprocess.run
        mock_subprocess_run = mocker.patch('cppython.plugins.conan.plugin.subprocess.run')
        mock_subprocess_run.return_value = mocker.Mock(returncode=0)

        # Mock getLogger
        mock_logger = mocker.Mock()
        mocker.patch('cppython.plugins.conan.plugin.getLogger', return_value=mock_logger)

        # Execute publish
        plugin.publish()

        # Verify subprocess.run was called with custom profiles
        mock_subprocess_run.assert_called_once()
        call_args = mock_subprocess_run.call_args[0][0]
        
        # Find profile arguments
        profile_host_idx = call_args.index('--profile:host')
        profile_build_idx = call_args.index('--profile:build')
        
        assert call_args[profile_host_idx + 1] == str(custom_host_profile)
        assert call_args[profile_build_idx + 1] == str(custom_build_profile)
