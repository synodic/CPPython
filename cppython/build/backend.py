"""PEP 517 build backend implementation wrapping scikit-build-core and meson-python.

This module provides the actual build hooks that delegate to the appropriate
underlying build backend (scikit-build-core for CMake, meson-python for Meson)
after running CPPython's preparation workflow.
"""

import logging
import tomllib
from pathlib import Path
from types import ModuleType
from typing import Any

import mesonpy
from scikit_build_core import build as skbuild

from cppython.build.prepare import BuildPreparationResult, prepare_build
from cppython.plugins.cmake.schema import CMakeSyncData
from cppython.plugins.meson.schema import MesonSyncData

logger = logging.getLogger('cppython.build')


def _is_meson_project() -> bool:
    """Detect if the current project uses Meson by checking pyproject.toml.

    Looks for ``[tool.cppython.generator]`` containing "meson" or the
    presence of a ``meson.build`` file in the source directory.

    Returns:
        True if the project appears to be Meson-based
    """
    source_dir = Path.cwd()

    # Check pyproject.toml for cppython generator configuration
    pyproject_path = source_dir / 'pyproject.toml'
    if pyproject_path.exists():
        with open(pyproject_path, 'rb') as f:
            data = tomllib.load(f)
        generator = data.get('tool', {}).get('cppython', {}).get('generator', '')
        if isinstance(generator, str) and 'meson' in generator.lower():
            return True

    # Fallback: check for meson.build file
    return (source_dir / 'meson.build').exists()


def _get_backend(is_meson: bool) -> ModuleType:
    """Get the appropriate backend module.

    Args:
        is_meson: Whether to use meson-python instead of scikit-build-core

    Returns:
        The backend module (mesonpy or scikit_build_core.build)
    """
    if is_meson:
        return mesonpy
    return skbuild


def _inject_cmake_toolchain(config_settings: dict[str, Any] | None, toolchain_file: Path | None) -> dict[str, Any]:
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


def _inject_meson_files(
    config_settings: dict[str, Any] | None,
    native_file: Path | None,
    cross_file: Path | None,
) -> dict[str, Any]:
    """Inject native/cross files into config settings for meson-python.

    Args:
        config_settings: The original config settings (may be None)
        native_file: Path to the Meson native file to inject
        cross_file: Path to the Meson cross file to inject

    Returns:
        Updated config settings with Meson files injected
    """
    settings = dict(config_settings) if config_settings else {}

    setup_args_key = 'setup-args'
    existing_args = settings.get(setup_args_key, '')

    args_to_add: list[str] = []

    if native_file and native_file.exists():
        native_arg = f'--native-file={native_file.absolute()}'
        if '--native-file' not in existing_args:
            args_to_add.append(native_arg)
            logger.info('CPPython: Injected --native-file=%s', native_file)
        else:
            logger.info('CPPython: User-specified native file takes precedence')

    if cross_file and cross_file.exists():
        cross_arg = f'--cross-file={cross_file.absolute()}'
        if '--cross-file' not in existing_args:
            args_to_add.append(cross_arg)
            logger.info('CPPython: Injected --cross-file=%s', cross_file)
        else:
            logger.info('CPPython: User-specified cross file takes precedence')

    if args_to_add:
        if existing_args:
            settings[setup_args_key] = f'{existing_args};' + ';'.join(args_to_add)
        else:
            settings[setup_args_key] = ';'.join(args_to_add)

    return settings


def _prepare_and_get_result(
    config_settings: dict[str, Any] | None,
) -> tuple[BuildPreparationResult, dict[str, Any]]:
    """Run CPPython preparation and merge config into settings.

    Args:
        config_settings: The original config settings

    Returns:
        Tuple of (preparation result, updated config settings)
    """
    # Determine source directory (current working directory during build)
    source_dir = Path.cwd()

    # Run CPPython preparation
    result = prepare_build(source_dir)

    # Inject settings based on sync data type
    settings = dict(config_settings) if config_settings else {}

    if result.sync_data is not None:
        if isinstance(result.sync_data, CMakeSyncData):
            settings = _inject_cmake_toolchain(settings, result.sync_data.toolchain_file)
        elif isinstance(result.sync_data, MesonSyncData):
            settings = _inject_meson_files(settings, result.sync_data.native_file, result.sync_data.cross_file)

    return result, settings


def _is_meson_build(result: BuildPreparationResult) -> bool:
    """Determine if the build should use meson-python based on sync data.

    Args:
        result: The build preparation result

    Returns:
        True if meson-python should be used, False for scikit-build-core
    """
    return isinstance(result.sync_data, MesonSyncData)


# PEP 517 Hooks - dispatching to the appropriate backend after preparation


def get_requires_for_build_wheel(config_settings: dict[str, Any] | None = None) -> list[str]:
    """Get additional requirements for building a wheel."""
    return _get_backend(_is_meson_project()).get_requires_for_build_wheel(config_settings)


def get_requires_for_build_sdist(config_settings: dict[str, Any] | None = None) -> list[str]:
    """Get additional requirements for building an sdist."""
    return _get_backend(_is_meson_project()).get_requires_for_build_sdist(config_settings)


def get_requires_for_build_editable(config_settings: dict[str, Any] | None = None) -> list[str]:
    """Get additional requirements for building an editable install."""
    return _get_backend(_is_meson_project()).get_requires_for_build_editable(config_settings)


def build_wheel(
    wheel_directory: str,
    config_settings: dict[str, Any] | None = None,
    metadata_directory: str | None = None,
) -> str:
    """Build a wheel, running CPPython preparation first."""
    logger.info('CPPython: Starting wheel build')
    result, settings = _prepare_and_get_result(config_settings)
    return _get_backend(_is_meson_build(result)).build_wheel(wheel_directory, settings, metadata_directory)


def build_sdist(
    sdist_directory: str,
    config_settings: dict[str, Any] | None = None,
) -> str:
    """Build a source distribution (no CPPython workflow needed)."""
    logger.info('CPPython: Starting sdist build')
    return _get_backend(_is_meson_project()).build_sdist(sdist_directory, config_settings)


def build_editable(
    wheel_directory: str,
    config_settings: dict[str, Any] | None = None,
    metadata_directory: str | None = None,
) -> str:
    """Build an editable wheel, running CPPython preparation first."""
    logger.info('CPPython: Starting editable build')
    result, settings = _prepare_and_get_result(config_settings)
    return _get_backend(_is_meson_build(result)).build_editable(wheel_directory, settings, metadata_directory)


def prepare_metadata_for_build_wheel(
    metadata_directory: str,
    config_settings: dict[str, Any] | None = None,
) -> str:
    """Prepare metadata for wheel build."""
    return _get_backend(_is_meson_project()).prepare_metadata_for_build_wheel(metadata_directory, config_settings)


def prepare_metadata_for_build_editable(
    metadata_directory: str,
    config_settings: dict[str, Any] | None = None,
) -> str:
    """Prepare metadata for editable build."""
    return _get_backend(_is_meson_project()).prepare_metadata_for_build_editable(metadata_directory, config_settings)
