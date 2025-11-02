"""Builder to help resolve cmake state"""

import os
from pathlib import Path
from typing import Any

from cppython.core.schema import CorePluginData
from cppython.plugins.cmake.schema import CMakeConfiguration, CMakeData


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
    cmake_binary: Path | None = None
    if env_binary := os.environ.get('CMAKE_BINARY'):
        cmake_binary = Path(env_binary)
    elif parsed_data.cmake_binary:
        cmake_binary = parsed_data.cmake_binary

    return CMakeData(
        preset_file=modified_preset_file, configuration_name=parsed_data.configuration_name, cmake_binary=cmake_binary
    )
