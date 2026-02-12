"""Meson plugin schema

This module defines the schema and data models for integrating the Meson
generator with CPPython. It includes definitions for configuration,
synchronization data, and resolved runtime data.
"""

from pathlib import Path
from typing import Annotated

from pydantic import Field

from cppython.core.schema import CPPythonModel, SyncData


class MesonSyncData(SyncData):
    """The Meson sync data exchanged between providers and the Meson generator.

    Providers populate these fields with paths to native/cross files
    that configure Meson to find provider-managed dependencies.
    """

    native_file: Annotated[
        Path | None,
        Field(
            description='Path to a Meson native file for same-platform builds. '
            'Contains pkg-config paths, dependency directories, and build options.'
        ),
    ] = None
    cross_file: Annotated[
        Path | None,
        Field(
            description='Path to a Meson cross file for cross-compilation. '
            'Contains host/target machine definitions and toolchain configuration.'
        ),
    ] = None


class MesonData(CPPythonModel):
    """Resolved Meson data used at runtime by the generator plugin."""

    build_file: Path
    build_directory: str
    meson_binary: Path | None


class MesonConfiguration(CPPythonModel):
    """Configuration for the Meson generator plugin.

    User-facing configuration from ``[tool.cppython.generators.meson]``.
    """

    build_file: Annotated[
        Path,
        Field(
            description='The meson.build file that defines the project. '
            'Relative paths are resolved against the project root.',
        ),
    ] = Path('meson.build')
    build_directory: Annotated[
        str,
        Field(
            description='The Meson build directory name. This is passed to '
            '"meson setup" as the build directory argument.',
        ),
    ] = 'builddir'
    meson_binary: Annotated[
        Path | None,
        Field(
            description='Path to a specific Meson binary to use. If not specified, uses "meson" from PATH. '
            'Can be overridden via MESON_BINARY environment variable.'
        ),
    ] = None
