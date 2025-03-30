"""Builder to help resolve cmake state"""

import json
from typing import Any

from cppython.core.schema import CorePluginData
from cppython.plugins.cmake.schema import CMakeConfiguration, CMakeData, CMakePresets


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

    modified_preset_dir = parsed_data.preset_file
    if not modified_preset_dir.is_absolute():
        modified_preset_dir = root_directory / modified_preset_dir

    # If the user hasn't specified a preset file, we need to create one
    if not modified_preset_dir.exists():
        modified_preset_dir.parent.mkdir(parents=True, exist_ok=True)
        with modified_preset_dir.open('w', encoding='utf-8') as file:
            presets_dict = CMakePresets().model_dump_json(exclude_none=True)
            json.dump(presets_dict, file, ensure_ascii=False, indent=4)

    return CMakeData(preset_file=modified_preset_dir, configuration_name=parsed_data.configuration_name)
