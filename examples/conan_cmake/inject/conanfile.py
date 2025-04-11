"""Preexisting CMake project with Conan integration."""

from conan import ConanFile  # type: ignore
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout  # type: ignore


class MyProject(ConanFile):  # type: ignore
    """Conan file for a simple CMake project."""

    name = 'myproject'
    version = '1.0'
    settings = 'os', 'compiler', 'build_type', 'arch'
    generators = 'CMakeDeps'

    def layout(self) -> None:
        """Define the layout of the project."""
        cmake_layout(self)

    def generate(self) -> None:
        """Generate the CMake toolchain file."""
        tc = CMakeToolchain(self)
        tc.generate()

    def build(self) -> None:
        """Build the project using CMake."""
        cmake = CMake(self)
        cmake.configure()
        cmake.build()
