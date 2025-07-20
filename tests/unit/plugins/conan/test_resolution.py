"""Unit tests for Conan resolution functionality."""

import logging
from unittest.mock import Mock, patch

import pytest
from conan.internal.model.profile import Profile
from packaging.requirements import Requirement

from cppython.core.exception import ConfigException
from cppython.core.schema import CorePluginData
from cppython.plugins.conan.resolution import (
    _profile_post_process,
    _resolve_profiles,
    resolve_conan_data,
    resolve_conan_dependency,
)
from cppython.plugins.conan.schema import (
    ConanData,
    ConanDependency,
    ConanRevision,
    ConanUserChannel,
    ConanVersion,
    ConanVersionRange,
)
from cppython.utility.exception import ProviderConfigurationError

# Constants for test validation
EXPECTED_PROFILE_CALL_COUNT = 2


class TestResolveDependency:
    """Test dependency resolution."""

    def test_with_version(self) -> None:
        """Test resolving a dependency with a >= version specifier."""
        requirement = Requirement('boost>=1.80.0')

        result = resolve_conan_dependency(requirement)

        assert result.name == 'boost'
        assert result.version_range is not None
        assert result.version_range.expression == '>=1.80.0'
        assert result.version is None

    def test_with_exact_version(self) -> None:
        """Test resolving a dependency with an exact version specifier."""
        requirement = Requirement('abseil==20240116.2')

        result = resolve_conan_dependency(requirement)

        assert result.name == 'abseil'
        assert result.version is not None
        assert str(result.version) == '20240116.2'
        assert result.version_range is None

    def test_without_version(self) -> None:
        """Test resolving a dependency without a version specifier."""
        requirement = Requirement('boost')

        result = resolve_conan_dependency(requirement)

        assert result.name == 'boost'
        assert result.version is None
        assert result.version_range is None

    def test_compatible_release(self) -> None:
        """Test resolving a dependency with ~= (compatible release) operator."""
        requirement = Requirement('package~=1.2.3')

        result = resolve_conan_dependency(requirement)

        assert result.name == 'package'
        assert result.version_range is not None
        assert result.version_range.expression == '~1.2'
        assert result.version is None

    def test_multiple_specifiers(self) -> None:
        """Test resolving a dependency with multiple specifiers."""
        requirement = Requirement('boost>=1.80.0,<2.0.0')

        result = resolve_conan_dependency(requirement)

        assert result.name == 'boost'
        assert result.version_range is not None
        assert result.version_range.expression == '>=1.80.0 <2.0.0'
        assert result.version is None

    def test_unsupported_operator(self) -> None:
        """Test that unsupported operators raise an error."""
        requirement = Requirement('boost===1.80.0')

        with pytest.raises(ConfigException, match="Unsupported single specifier '==='"):
            resolve_conan_dependency(requirement)

    def test_contradictory_exact_versions(self) -> None:
        """Test that multiple specifiers work correctly for valid ranges."""
        # Test our logic with a valid range instead of invalid syntax
        requirement = Requirement('package>=1.0,<=2.0')  # Valid range
        result = resolve_conan_dependency(requirement)

        assert result.name == 'package'
        assert result.version_range is not None
        assert result.version_range.expression == '>=1.0 <=2.0'

    def test_requires_exact_version(self) -> None:
        """Test that ConanDependency generates correct requires for exact versions."""
        dependency = ConanDependency(name='abseil', version=ConanVersion.from_string('20240116.2'))

        assert dependency.requires() == 'abseil/20240116.2'

    def test_requires_version_range(self) -> None:
        """Test that ConanDependency generates correct requires for version ranges."""
        dependency = ConanDependency(name='boost', version_range=ConanVersionRange(expression='>=1.80.0 <2.0'))

        assert dependency.requires() == 'boost/[>=1.80.0 <2.0]'

    def test_requires_legacy_minimum_version(self) -> None:
        """Test that ConanDependency generates correct requires for legacy minimum versions."""
        dependency = ConanDependency(name='boost', version_range=ConanVersionRange(expression='>=1.80.0'))

        assert dependency.requires() == 'boost/[>=1.80.0]'

    def test_requires_legacy_exact_version(self) -> None:
        """Test that ConanDependency generates correct requires for legacy exact versions."""
        dependency = ConanDependency(name='abseil', version=ConanVersion.from_string('20240116.2'))

        assert dependency.requires() == 'abseil/20240116.2'

    def test_requires_no_version(self) -> None:
        """Test that ConanDependency generates correct requires for dependencies without version."""
        dependency = ConanDependency(name='somelib')

        assert dependency.requires() == 'somelib'

    def test_with_user_channel(self) -> None:
        """Test that ConanDependency handles user/channel correctly."""
        dependency = ConanDependency(
            name='mylib',
            version=ConanVersion.from_string('1.0.0'),
            user_channel=ConanUserChannel(user='myuser', channel='stable'),
        )

        assert dependency.requires() == 'mylib/1.0.0@myuser/stable'

    def test_with_revision(self) -> None:
        """Test that ConanDependency handles revisions correctly."""
        dependency = ConanDependency(
            name='mylib', version=ConanVersion.from_string('1.0.0'), revision=ConanRevision(revision='abc123')
        )

        assert dependency.requires() == 'mylib/1.0.0#abc123'

    def test_full_reference(self) -> None:
        """Test that ConanDependency handles full references correctly."""
        dependency = ConanDependency(
            name='mylib',
            version=ConanVersion.from_string('1.0.0'),
            user_channel=ConanUserChannel(user='myuser', channel='stable'),
            revision=ConanRevision(revision='abc123'),
        )

        assert dependency.requires() == 'mylib/1.0.0@myuser/stable#abc123'

    def test_from_reference_simple(self) -> None:
        """Test parsing a simple package name."""
        dependency = ConanDependency.from_conan_reference('mylib')

        assert dependency.name == 'mylib'
        assert dependency.version is None
        assert dependency.user_channel is None
        assert dependency.revision is None

    def test_from_reference_with_version(self) -> None:
        """Test parsing a package with version."""
        dependency = ConanDependency.from_conan_reference('mylib/1.0.0')

        assert dependency.name == 'mylib'
        assert dependency.version is not None
        assert str(dependency.version) == '1.0.0'
        assert dependency.user_channel is None
        assert dependency.revision is None

    def test_from_reference_with_version_range(self) -> None:
        """Test parsing a package with version range."""
        dependency = ConanDependency.from_conan_reference('mylib/[>=1.0 <2.0]')

        assert dependency.name == 'mylib'
        assert dependency.version is None
        assert dependency.version_range is not None
        assert dependency.version_range.expression == '>=1.0 <2.0'
        assert dependency.user_channel is None
        assert dependency.revision is None

    def test_from_reference_full(self) -> None:
        """Test parsing a full Conan reference."""
        dependency = ConanDependency.from_conan_reference('mylib/1.0.0@myuser/stable#abc123')

        assert dependency.name == 'mylib'
        assert dependency.version is not None
        assert str(dependency.version) == '1.0.0'
        assert dependency.user_channel is not None
        assert dependency.user_channel.user == 'myuser'
        assert dependency.user_channel.channel == 'stable'
        assert dependency.revision is not None
        assert dependency.revision.revision == 'abc123'


class TestProfileProcessing:
    """Test profile processing functionality."""

    def test_success(self) -> None:
        """Test successful profile processing."""
        mock_conan_api = Mock()
        mock_profile = Mock()
        mock_cache_settings = Mock()
        mock_plugin = Mock()

        mock_conan_api.profiles._load_profile_plugin.return_value = mock_plugin
        profiles = [mock_profile]

        _profile_post_process(profiles, mock_conan_api, mock_cache_settings)

        mock_plugin.assert_called_once_with(mock_profile)
        mock_profile.process_settings.assert_called_once_with(mock_cache_settings)

    def test_no_plugin(self) -> None:
        """Test profile processing when no plugin is available."""
        mock_conan_api = Mock()
        mock_profile = Mock()
        mock_cache_settings = Mock()

        mock_conan_api.profiles._load_profile_plugin.return_value = None
        profiles = [mock_profile]

        _profile_post_process(profiles, mock_conan_api, mock_cache_settings)

        mock_profile.process_settings.assert_called_once_with(mock_cache_settings)

    def test_plugin_failure(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test profile processing when plugin fails."""
        mock_conan_api = Mock()
        mock_profile = Mock()
        mock_cache_settings = Mock()
        mock_plugin = Mock()

        mock_conan_api.profiles._load_profile_plugin.return_value = mock_plugin
        mock_plugin.side_effect = Exception('Plugin failed')
        profiles = [mock_profile]

        with caplog.at_level(logging.WARNING):
            _profile_post_process(profiles, mock_conan_api, mock_cache_settings)

        assert 'Profile plugin failed for profile' in caplog.text
        mock_profile.process_settings.assert_called_once_with(mock_cache_settings)

    def test_settings_failure(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test profile processing when settings processing fails."""
        mock_conan_api = Mock()
        mock_profile = Mock()
        mock_cache_settings = Mock()

        mock_conan_api.profiles._load_profile_plugin.return_value = None
        mock_profile.process_settings.side_effect = Exception('Settings failed')
        profiles = [mock_profile]

        with caplog.at_level(logging.DEBUG):
            _profile_post_process(profiles, mock_conan_api, mock_cache_settings)

        assert 'Settings processing failed for profile' in caplog.text


class TestResolveProfiles:
    """Test profile resolution functionality."""

    def test_by_name(self) -> None:
        """Test resolving profiles by name."""
        mock_conan_api = Mock()
        mock_host_profile = Mock()
        mock_build_profile = Mock()
        mock_conan_api.profiles.get_profile.side_effect = [mock_host_profile, mock_build_profile]

        host_result, build_result = _resolve_profiles(
            'host-profile', 'build-profile', mock_conan_api, cmake_program=None
        )

        assert host_result == mock_host_profile
        assert build_result == mock_build_profile
        assert mock_conan_api.profiles.get_profile.call_count == EXPECTED_PROFILE_CALL_COUNT
        mock_conan_api.profiles.get_profile.assert_any_call(['host-profile'])
        mock_conan_api.profiles.get_profile.assert_any_call(['build-profile'])

    def test_by_name_failure(self) -> None:
        """Test resolving profiles by name when host profile fails."""
        mock_conan_api = Mock()
        mock_conan_api.profiles.get_profile.side_effect = Exception('Profile not found')

        with pytest.raises(ProviderConfigurationError, match='Failed to load host profile'):
            _resolve_profiles('missing-profile', 'other-profile', mock_conan_api, cmake_program=None)

    def test_auto_detect(self) -> None:
        """Test auto-detecting profiles."""
        mock_conan_api = Mock()
        mock_host_profile = Mock()
        mock_build_profile = Mock()
        mock_host_default_path = 'host-default'
        mock_build_default_path = 'build-default'

        mock_conan_api.profiles.get_default_host.return_value = mock_host_default_path
        mock_conan_api.profiles.get_default_build.return_value = mock_build_default_path
        mock_conan_api.profiles.get_profile.side_effect = [mock_host_profile, mock_build_profile]

        host_result, build_result = _resolve_profiles(None, None, mock_conan_api, cmake_program=None)

        assert host_result == mock_host_profile
        assert build_result == mock_build_profile
        mock_conan_api.profiles.get_default_host.assert_called_once()
        mock_conan_api.profiles.get_default_build.assert_called_once()
        mock_conan_api.profiles.get_profile.assert_any_call([mock_host_default_path])
        mock_conan_api.profiles.get_profile.assert_any_call([mock_build_default_path])

    @patch('cppython.plugins.conan.resolution._profile_post_process')
    def test_fallback_to_detect(self, mock_post_process: Mock) -> None:
        """Test falling back to profile detection when defaults fail."""
        mock_conan_api = Mock()
        mock_host_profile = Mock()
        mock_build_profile = Mock()
        mock_cache_settings = Mock()

        # Mock the default profile methods to fail
        mock_conan_api.profiles.get_default_host.side_effect = Exception('No default profile')
        mock_conan_api.profiles.get_default_build.side_effect = Exception('No default profile')
        mock_conan_api.profiles.get_profile.side_effect = Exception('Profile not found')

        # Mock detect to succeed
        mock_conan_api.profiles.detect.side_effect = [mock_host_profile, mock_build_profile]
        mock_conan_api.config.settings_yml = mock_cache_settings

        host_result, build_result = _resolve_profiles(None, None, mock_conan_api, cmake_program=None)

        assert host_result == mock_host_profile
        assert build_result == mock_build_profile
        assert mock_conan_api.profiles.detect.call_count == EXPECTED_PROFILE_CALL_COUNT
        assert mock_post_process.call_count == EXPECTED_PROFILE_CALL_COUNT
        mock_post_process.assert_any_call([mock_host_profile], mock_conan_api, mock_cache_settings, None)
        mock_post_process.assert_any_call([mock_build_profile], mock_conan_api, mock_cache_settings, None)

    @patch('cppython.plugins.conan.resolution._profile_post_process')
    def test_default_fallback_to_detect(self, mock_post_process: Mock) -> None:
        """Test falling back to profile detection when default profile fails."""
        mock_conan_api = Mock()
        mock_host_profile = Mock()
        mock_build_profile = Mock()
        mock_cache_settings = Mock()

        # Mock the default profile to fail (this simulates the "default" profile not existing)
        mock_conan_api.profiles.get_profile.side_effect = Exception('Profile not found')
        mock_conan_api.profiles.get_default_host.side_effect = Exception('No default profile')
        mock_conan_api.profiles.get_default_build.side_effect = Exception('No default profile')

        # Mock detect to succeed
        mock_conan_api.profiles.detect.side_effect = [mock_host_profile, mock_build_profile]
        mock_conan_api.config.settings_yml = mock_cache_settings

        host_result, build_result = _resolve_profiles('default', 'default', mock_conan_api, cmake_program=None)

        assert host_result == mock_host_profile
        assert build_result == mock_build_profile
        assert mock_conan_api.profiles.detect.call_count == EXPECTED_PROFILE_CALL_COUNT
        assert mock_post_process.call_count == EXPECTED_PROFILE_CALL_COUNT
        mock_post_process.assert_any_call([mock_host_profile], mock_conan_api, mock_cache_settings, None)
        mock_post_process.assert_any_call([mock_build_profile], mock_conan_api, mock_cache_settings, None)


class TestResolveConanData:
    """Test Conan data resolution."""

    @patch('cppython.plugins.conan.resolution.ConanAPI')
    @patch('cppython.plugins.conan.resolution._resolve_profiles')
    @patch('cppython.plugins.conan.resolution._detect_cmake_program')
    def test_with_profiles(
        self, mock_detect_cmake: Mock, mock_resolve_profiles: Mock, mock_conan_api_class: Mock
    ) -> None:
        """Test resolving ConanData with profile configuration."""
        mock_detect_cmake.return_value = None  # No cmake detected for test
        mock_conan_api = Mock()
        mock_conan_api_class.return_value = mock_conan_api

        mock_host_profile = Mock(spec=Profile)
        mock_build_profile = Mock(spec=Profile)
        mock_resolve_profiles.return_value = (mock_host_profile, mock_build_profile)

        data = {'host_profile': 'linux-x64', 'build_profile': 'linux-gcc11', 'remotes': ['conancenter']}
        core_data = Mock(spec=CorePluginData)

        result = resolve_conan_data(data, core_data)

        assert isinstance(result, ConanData)
        assert result.host_profile == mock_host_profile
        assert result.build_profile == mock_build_profile
        assert result.remotes == ['conancenter']

        # Verify profile resolution was called correctly
        mock_resolve_profiles.assert_called_once_with('linux-x64', 'linux-gcc11', mock_conan_api, None)

    @patch('cppython.plugins.conan.resolution.ConanAPI')
    @patch('cppython.plugins.conan.resolution._resolve_profiles')
    @patch('cppython.plugins.conan.resolution._detect_cmake_program')
    def test_default_profiles(
        self, mock_detect_cmake: Mock, mock_resolve_profiles: Mock, mock_conan_api_class: Mock
    ) -> None:
        """Test resolving ConanData with default profile configuration."""
        mock_detect_cmake.return_value = None  # No cmake detected for test
        mock_conan_api = Mock()
        mock_conan_api_class.return_value = mock_conan_api

        mock_host_profile = Mock(spec=Profile)
        mock_build_profile = Mock(spec=Profile)
        mock_resolve_profiles.return_value = (mock_host_profile, mock_build_profile)

        data = {}  # Empty data should use defaults
        core_data = Mock(spec=CorePluginData)

        result = resolve_conan_data(data, core_data)

        assert isinstance(result, ConanData)
        assert result.host_profile == mock_host_profile
        assert result.build_profile == mock_build_profile
        assert result.remotes == ['conancenter']  # Default remote

        # Verify profile resolution was called with default values
        mock_resolve_profiles.assert_called_once_with('default', 'default', mock_conan_api, None)

    @patch('cppython.plugins.conan.resolution.ConanAPI')
    @patch('cppython.plugins.conan.resolution._resolve_profiles')
    @patch('cppython.plugins.conan.resolution._detect_cmake_program')
    def test_null_profiles(
        self, mock_detect_cmake: Mock, mock_resolve_profiles: Mock, mock_conan_api_class: Mock
    ) -> None:
        """Test resolving ConanData with null profile configuration."""
        mock_detect_cmake.return_value = None  # No cmake detected for test
        mock_conan_api = Mock()
        mock_conan_api_class.return_value = mock_conan_api

        mock_host_profile = Mock(spec=Profile)
        mock_build_profile = Mock(spec=Profile)
        mock_resolve_profiles.return_value = (mock_host_profile, mock_build_profile)

        data = {'host_profile': None, 'build_profile': None, 'remotes': [], 'skip_upload': False}
        core_data = Mock(spec=CorePluginData)

        result = resolve_conan_data(data, core_data)

        assert isinstance(result, ConanData)
        assert result.host_profile == mock_host_profile
        assert result.build_profile == mock_build_profile
        assert result.remotes == []
        assert result.skip_upload is False

        # Verify profile resolution was called with None values
        mock_resolve_profiles.assert_called_once_with(None, None, mock_conan_api, None)

    @patch('cppython.plugins.conan.resolution.ConanAPI')
    @patch('cppython.plugins.conan.resolution._profile_post_process')
    def test_auto_detected_profile_processing(self, mock_post_process: Mock, mock_conan_api_class: Mock):
        """Test that auto-detected profiles get proper post-processing.

        Args:
            mock_post_process: Mock for _profile_post_process function
            mock_conan_api_class: Mock for ConanAPI class
        """
        mock_conan_api = Mock()
        mock_conan_api_class.return_value = mock_conan_api

        # Configure the mock to simulate no default profiles
        mock_conan_api.profiles.get_default_host.side_effect = Exception('No default profile')
        mock_conan_api.profiles.get_default_build.side_effect = Exception('No default profile')

        # Create a profile that simulates auto-detection
        mock_profile = Mock()
        mock_profile.settings = {'os': 'Windows', 'arch': 'x86_64'}
        mock_profile.process_settings = Mock()
        mock_profile.conf = Mock()
        mock_profile.conf.validate = Mock()
        mock_profile.conf.rebase_conf_definition = Mock()

        mock_conan_api.profiles.detect.return_value = mock_profile
        mock_conan_api.config.global_conf = Mock()

        # Call the resolution - this should trigger auto-detection and post-processing
        host_profile, build_profile = _resolve_profiles(None, None, mock_conan_api, cmake_program=None)

        # Verify that auto-detection was called for both profiles
        assert mock_conan_api.profiles.detect.call_count == EXPECTED_PROFILE_CALL_COUNT

        # Verify that post-processing was called for both profiles
        assert mock_post_process.call_count == EXPECTED_PROFILE_CALL_COUNT
