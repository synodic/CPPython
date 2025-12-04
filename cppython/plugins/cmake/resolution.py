"""Builder to help resolve cmake state"""

import logging
import os
import shutil
from pathlib import Path
from typing import Any

from cppython.core.schema import CorePluginData
from cppython.plugins.cmake.schema import CMakeConfiguration, CMakeData


def _resolve_cmake_binary(configured_path: Path | None) -> Path | None:
    """Resolve the cmake binary path with validation.

    Resolution order:
    1. CMAKE_BINARY environment variable (highest priority)
    2. Configured path from cmake_binary setting
    3. cmake from PATH (fallback)

    If a path is specified (via env or config) but doesn't exist,
    a warning is logged and we fall back to PATH lookup.

    Args:
        configured_path: The cmake_binary path from configuration, if any

    Returns:
        Resolved cmake path, or None if not found anywhere
    """
    logger = logging.getLogger('cppython.cmake')

    # Environment variable takes precedence
    if env_binary := os.environ.get('CMAKE_BINARY'):
        env_path = Path(env_binary)
        if env_path.exists():
            return env_path
        logger.warning(
            'CMAKE_BINARY environment variable points to non-existent path: %s. '
            'Falling back to PATH lookup.',
            env_binary,
        )

    # Try configured path
    if configured_path:
        if configured_path.exists():
            return configured_path
        logger.warning(
            'Configured cmake_binary path does not exist: %s. '
            'Falling back to PATH lookup.',
            configured_path,
        )

    # Fall back to PATH lookup
    if cmake_in_path := shutil.which('cmake'):
        return Path(cmake_in_path)

    return None


def resolve_cmake_data(data: dict[str, Any], core_data: CorePluginData) -> CMakeData:
    """Resolves the input data table from defaults to requirements

    Args:
        data: The input table
        core_data: The core data to help with the resolve

    Returns:
        The resolved data
    """
    parsed_data = CMakeConfiguration(**data)

    root_directory = core_data.project_data.project_root.absolute()

    modified_preset_file = parsed_data.preset_file
    if not modified_preset_file.is_absolute():
        modified_preset_file = root_directory / modified_preset_file

    # Resolve cmake binary: environment variable takes precedence over configuration
    cmake_binary = _resolve_cmake_binary(parsed_data.cmake_binary)

    return CMakeData(
        preset_file=modified_preset_file, configuration_name=parsed_data.configuration_name, cmake_binary=cmake_binary
    )
