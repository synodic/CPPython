"""Builder to help resolve meson state"""

import logging
import os
import shutil
from pathlib import Path
from typing import Any

from cppython.core.schema import CorePluginData
from cppython.plugins.meson.schema import MesonConfiguration, MesonData


def _resolve_meson_binary(configured_path: Path | None) -> Path | None:
    """Resolve the meson binary path with validation.

    Resolution order:
    1. MESON_BINARY environment variable (highest priority)
    2. Configured path from meson_binary setting
    3. meson from PATH (fallback)

    If a path is specified (via env or config) but doesn't exist,
    a warning is logged and we fall back to PATH lookup.

    Args:
        configured_path: The meson_binary path from configuration, if any

    Returns:
        Resolved meson path, or None if not found anywhere
    """
    logger = logging.getLogger('cppython.meson')

    # Environment variable takes precedence
    if env_binary := os.environ.get('MESON_BINARY'):
        env_path = Path(env_binary)
        if env_path.exists():
            return env_path
        logger.warning(
            'MESON_BINARY environment variable points to non-existent path: %s. Falling back to PATH lookup.',
            env_binary,
        )

    # Try configured path
    if configured_path:
        if configured_path.exists():
            return configured_path
        logger.warning(
            'Configured meson_binary path does not exist: %s. Falling back to PATH lookup.',
            configured_path,
        )

    # Fall back to PATH lookup
    if meson_in_path := shutil.which('meson'):
        return Path(meson_in_path)

    return None


def resolve_meson_data(data: dict[str, Any], core_data: CorePluginData) -> MesonData:
    """Resolves the input data table from defaults to requirements.

    Args:
        data: The input table
        core_data: The core data to help with the resolve

    Returns:
        The resolved data
    """
    parsed_data = MesonConfiguration(**data)

    root_directory = core_data.project_data.project_root.absolute()

    modified_build_file = parsed_data.build_file
    if not modified_build_file.is_absolute():
        modified_build_file = root_directory / modified_build_file

    # Resolve meson binary: environment variable takes precedence over configuration
    meson_binary = _resolve_meson_binary(parsed_data.meson_binary)

    return MesonData(
        build_file=modified_build_file, build_directory=parsed_data.build_directory, meson_binary=meson_binary
    )
