"""Builder to help resolve cmake state"""

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

    return CMakeData(preset_file=modified_preset_file, configuration_name=parsed_data.configuration_name)
