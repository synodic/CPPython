"""Test package for mathutils library."""

import os

from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout


class MathUtilsTestConan(ConanFile):
    """Test package for mathutils library."""

    settings = 'os', 'compiler', 'build_type', 'arch'

    def requirements(self):
        """Add the tested package as a requirement."""
        self.requires(self.tested_reference_str)

    def layout(self):
        """Set the CMake layout."""
        cmake_layout(self)

    def generate(self):
        """Generate CMake dependencies and toolchain."""
        deps = CMakeDeps(self)
        deps.generate()
        tc = CMakeToolchain(self)
        tc.generate()

    def build(self):
        """Build the test package."""
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def test(self):
        """Run the test."""
        if can_run(self):
            cmd = os.path.join(self.cpp.build.bindir, 'consumer')
            self.run(cmd, env='conanrun')
