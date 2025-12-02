"""CPPython build backend wrapping scikit-build-core.

This module provides PEP 517/518 build backend hooks that wrap scikit-build-core,
automatically running CPPython's provider workflow before building
to inject the generated toolchain file into the CMake configuration.

Usage in pyproject.toml:
    [build-system]
    requires = ["cppython[conan, cmake]"]
    build-backend = "cppython.build"
"""

from cppython.build.backend import (
    build_editable,
    build_sdist,
    build_wheel,
    get_requires_for_build_editable,
    get_requires_for_build_sdist,
    get_requires_for_build_wheel,
    prepare_metadata_for_build_editable,
    prepare_metadata_for_build_wheel,
)

__all__ = [
    'build_editable',
    'build_sdist',
    'build_wheel',
    'get_requires_for_build_editable',
    'get_requires_for_build_sdist',
    'get_requires_for_build_wheel',
    'prepare_metadata_for_build_editable',
    'prepare_metadata_for_build_wheel',
]
