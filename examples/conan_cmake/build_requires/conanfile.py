"""Conan recipe demonstrating tool_requires with CMake and abseil dependency.

This example shows how to use tool_requires to specify build-time dependencies
like CMake, while using regular requires for runtime dependencies like abseil.
"""

from conan import ConanFile
from conan.tools.cmake import CMake, cmake_layout


class BuildRequiresExample(ConanFile):
    """Example Conan recipe demonstrating tool_requires with CMake and abseil."""

    name = 'build_requires_example'
    version = '1.0'

    # Basic package configuration
    settings = 'os', 'compiler', 'build_type', 'arch'

    # Regular dependencies - libraries we link against
    requires = 'abseil/20240116.2'

    # Build dependencies - tools needed during build
    tool_requires = 'cmake/[>=3.24]'

    # Generators for CMake integration
    generators = 'CMakeToolchain', 'CMakeDeps'

    def layout(self):
        """Define the layout for the project."""
        cmake_layout(self)

    def configure(self):
        """Configure package options based on settings."""
        # Example: Configure abseil options if needed
        # self.options["abseil"].shared = False
        pass

    def build_requirements(self):
        """Additional build requirements logic if needed."""
        # This method can be used for conditional build requirements
        # For example, only require certain tools on specific platforms
        pass

    def build(self):
        """Build the project using CMake."""
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        """Package the built artifacts."""
        cmake = CMake(self)
        cmake.install()
