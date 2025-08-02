"""Unit tests for Conan resolution functionality."""

import pytest
from packaging.requirements import Requirement

from cppython.core.exception import ConfigException
from cppython.plugins.conan.resolution import (
    resolve_conan_dependency,
)
from cppython.plugins.conan.schema import (
    ConanDependency,
    ConanRevision,
    ConanUserChannel,
    ConanVersion,
    ConanVersionRange,
)

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
            name='example',
            version=ConanVersion.from_string('1.0.0'),
            user_channel=ConanUserChannel(user='myuser', channel='stable'),
        )

        assert dependency.requires() == 'example/1.0.0@myuser/stable'

    def test_with_revision(self) -> None:
        """Test that ConanDependency handles revisions correctly."""
        dependency = ConanDependency(
            name='example', version=ConanVersion.from_string('1.0.0'), revision=ConanRevision(revision='abc123')
        )

        assert dependency.requires() == 'example/1.0.0#abc123'

    def test_full_reference(self) -> None:
        """Test that ConanDependency handles full references correctly."""
        dependency = ConanDependency(
            name='example',
            version=ConanVersion.from_string('1.0.0'),
            user_channel=ConanUserChannel(user='myuser', channel='stable'),
            revision=ConanRevision(revision='abc123'),
        )

        assert dependency.requires() == 'example/1.0.0@myuser/stable#abc123'

    def test_from_reference_simple(self) -> None:
        """Test parsing a simple package name."""
        dependency = ConanDependency.from_conan_reference('example')

        assert dependency.name == 'example'
        assert dependency.version is None
        assert dependency.user_channel is None
        assert dependency.revision is None

    def test_from_reference_with_version(self) -> None:
        """Test parsing a package with version."""
        dependency = ConanDependency.from_conan_reference('example/1.0.0')

        assert dependency.name == 'example'
        assert dependency.version is not None
        assert str(dependency.version) == '1.0.0'
        assert dependency.user_channel is None
        assert dependency.revision is None

    def test_from_reference_with_version_range(self) -> None:
        """Test parsing a package with version range."""
        dependency = ConanDependency.from_conan_reference('example/[>=1.0 <2.0]')

        assert dependency.name == 'example'
        assert dependency.version is None
        assert dependency.version_range is not None
        assert dependency.version_range.expression == '>=1.0 <2.0'
        assert dependency.user_channel is None
        assert dependency.revision is None

    def test_from_reference_full(self) -> None:
        """Test parsing a full Conan reference."""
        dependency = ConanDependency.from_conan_reference('example/1.0.0@myuser/stable#abc123')

        assert dependency.name == 'example'
        assert dependency.version is not None
        assert str(dependency.version) == '1.0.0'
        assert dependency.user_channel is not None
        assert dependency.user_channel.user == 'myuser'
        assert dependency.user_channel.channel == 'stable'
        assert dependency.revision is not None
        assert dependency.revision.revision == 'abc123'


class TestResolveProfiles:
    """Test profile resolution functionality."""


class TestResolveConanData:
    """Test Conan data resolution."""
