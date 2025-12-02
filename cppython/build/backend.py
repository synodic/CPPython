"""PEP 517 build backend implementation wrapping scikit-build-core.

This module provides the actual build hooks that delegate to scikit-build-core
after running CPPython's preparation workflow.
"""

import logging
from pathlib import Path
from typing import Any

from scikit_build_core import build as skbuild

from cppython.build.prepare import prepare_build

logger = logging.getLogger('cppython.build')


def _inject_toolchain(config_settings: dict[str, Any] | None, toolchain_file: Path | None) -> dict[str, Any]:
    """Inject the toolchain file into config settings for scikit-build-core.

    Args:
        config_settings: The original config settings (may be None)
        toolchain_file: Path to the toolchain file to inject

    Returns:
        Updated config settings with toolchain file injected
    """
    settings = dict(config_settings) if config_settings else {}

    if toolchain_file and toolchain_file.exists():
        # scikit-build-core accepts cmake.args for passing CMake arguments
        # Using cmake.args passes the toolchain via -DCMAKE_TOOLCHAIN_FILE=...
        args_key = 'cmake.args'
        toolchain_arg = f'-DCMAKE_TOOLCHAIN_FILE={toolchain_file.absolute()}'

        # Append to existing args or create new
        if args_key in settings:
            existing = settings[args_key]
            # Check if toolchain is already specified
            if 'CMAKE_TOOLCHAIN_FILE' not in existing:
                settings[args_key] = f'{existing};{toolchain_arg}'
                logger.info('CPPython: Appended CMAKE_TOOLCHAIN_FILE to cmake.args')
            else:
                logger.info('CPPython: User-specified toolchain file takes precedence')
        else:
            settings[args_key] = toolchain_arg
            logger.info('CPPython: Injected CMAKE_TOOLCHAIN_FILE=%s', toolchain_file)

    return settings


def _prepare_and_get_settings(
    config_settings: dict[str, Any] | None,
) -> dict[str, Any]:
    """Run CPPython preparation and merge toolchain into config settings.

    Args:
        config_settings: The original config settings

    Returns:
        Config settings with CPPython toolchain injected
    """
    # Determine source directory (current working directory during build)
    source_dir = Path.cwd()

    # Run CPPython preparation
    toolchain_file = prepare_build(source_dir)

    # Inject toolchain into config settings
    return _inject_toolchain(config_settings, toolchain_file)


# PEP 517 Hooks - delegating to scikit-build-core after preparation


def get_requires_for_build_wheel(
    config_settings: dict[str, Any] | None = None,
) -> list[str]:
    """Get additional requirements for building a wheel.

    Args:
        config_settings: Build configuration settings

    Returns:
        List of additional requirements
    """
    return skbuild.get_requires_for_build_wheel(config_settings)


def get_requires_for_build_sdist(
    config_settings: dict[str, Any] | None = None,
) -> list[str]:
    """Get additional requirements for building an sdist.

    Args:
        config_settings: Build configuration settings

    Returns:
        List of additional requirements
    """
    return skbuild.get_requires_for_build_sdist(config_settings)


def get_requires_for_build_editable(
    config_settings: dict[str, Any] | None = None,
) -> list[str]:
    """Get additional requirements for building an editable install.

    Args:
        config_settings: Build configuration settings

    Returns:
        List of additional requirements
    """
    return skbuild.get_requires_for_build_editable(config_settings)


def build_wheel(
    wheel_directory: str,
    config_settings: dict[str, Any] | None = None,
    metadata_directory: str | None = None,
) -> str:
    """Build a wheel from the source distribution.

    This runs CPPython's provider workflow first to ensure C++ dependencies
    are installed and the toolchain file is generated, then delegates to
    scikit-build-core for the actual wheel build.

    Args:
        wheel_directory: Directory to place the built wheel
        config_settings: Build configuration settings
        metadata_directory: Directory containing wheel metadata

    Returns:
        The basename of the built wheel
    """
    logger.info('CPPython: Starting wheel build')

    # Prepare CPPython and get updated settings
    settings = _prepare_and_get_settings(config_settings)

    # Delegate to scikit-build-core
    return skbuild.build_wheel(wheel_directory, settings, metadata_directory)


def build_sdist(
    sdist_directory: str,
    config_settings: dict[str, Any] | None = None,
) -> str:
    """Build a source distribution.

    For sdist, we don't run the full CPPython workflow since the C++ dependencies
    should be resolved at wheel build time, not sdist creation time.

    Args:
        sdist_directory: Directory to place the built sdist
        config_settings: Build configuration settings

    Returns:
        The basename of the built sdist
    """
    logger.info('CPPython: Starting sdist build')

    # Delegate directly to scikit-build-core (no preparation needed for sdist)
    return skbuild.build_sdist(sdist_directory, config_settings)


def build_editable(
    wheel_directory: str,
    config_settings: dict[str, Any] | None = None,
    metadata_directory: str | None = None,
) -> str:
    """Build an editable wheel.

    This runs CPPython's provider workflow first, similar to build_wheel.

    Args:
        wheel_directory: Directory to place the built wheel
        config_settings: Build configuration settings
        metadata_directory: Directory containing wheel metadata

    Returns:
        The basename of the built wheel
    """
    logger.info('CPPython: Starting editable build')

    # Prepare CPPython and get updated settings
    settings = _prepare_and_get_settings(config_settings)

    # Delegate to scikit-build-core
    return skbuild.build_editable(wheel_directory, settings, metadata_directory)


def prepare_metadata_for_build_wheel(
    metadata_directory: str,
    config_settings: dict[str, Any] | None = None,
) -> str:
    """Prepare metadata for wheel build.

    Args:
        metadata_directory: Directory to place the metadata
        config_settings: Build configuration settings

    Returns:
        The basename of the metadata directory
    """
    return skbuild.prepare_metadata_for_build_wheel(metadata_directory, config_settings)


def prepare_metadata_for_build_editable(
    metadata_directory: str,
    config_settings: dict[str, Any] | None = None,
) -> str:
    """Prepare metadata for editable build.

    Args:
        metadata_directory: Directory to place the metadata
        config_settings: Build configuration settings

    Returns:
        The basename of the metadata directory
    """
    return skbuild.prepare_metadata_for_build_editable(metadata_directory, config_settings)
