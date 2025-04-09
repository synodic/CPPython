"""Unit tests for the Vcpkg resolution plugin."""

from packaging.requirements import Requirement

from cppython.plugins.vcpkg.resolution import resolve_vcpkg_dependency


class TestVcpkgResolution:
    """Test the resolution of Vcpkg dependencies"""

    @staticmethod
    def test_resolve_vcpkg_dependency() -> None:
        """Test resolving a VcpkgDependency from a packaging requirement."""
        requirement = Requirement('example-package>=1.2.3')

        dependency = resolve_vcpkg_dependency(requirement)

        assert dependency.name == 'example-package'
        assert dependency.version_ge == '1.2.3'
        assert dependency.default_features is True
        assert dependency.features == []
        assert dependency.platform is None
        assert dependency.host is False
