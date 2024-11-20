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

    root_directory = core_data.project_data.pyproject_file.parent.absolute()

    modified_preset = parsed_data.preset_file
    if not modified_preset.is_absolute():
        modified_preset = root_directory / modified_preset

    return CMakeData(preset_file=modified_preset, configuration_name=parsed_data.configuration_name)
