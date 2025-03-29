"""Plugin builder"""

import json
from copy import deepcopy
from pathlib import Path

from cppython.plugins.cmake.schema import CMakePresets, CMakeSyncData, ConfigurePreset


class Builder:
    """Aids in building the information needed for the CMake plugin"""

    @staticmethod
    def write_provider_preset(provider_directory: Path, data: CMakeSyncData) -> None:
        """Writes a provider preset from input sync data

        Args:
            provider_directory: The base directory to place the preset files
            data: The providers synchronization data
        """
        configure_preset = ConfigurePreset(name=data.provider_name, cacheVariables=None)
        presets = CMakePresets(configurePresets=[configure_preset])

        json_path = provider_directory / f'{data.provider_name}.json'

        serialized = json.loads(presets.model_dump_json(exclude_none=True, by_alias=False))
        with open(json_path, 'w', encoding='utf8') as file:
            json.dump(serialized, file, ensure_ascii=False, indent=4)

    @staticmethod
    def write_cppython_preset(
        cppython_preset_directory: Path, _provider_directory: Path, _provider_data: CMakeSyncData
    ) -> Path:
        """Write the cppython presets which inherit from the provider presets

        Args:
            cppython_preset_directory: The tool directory

        Returns:
            A file path to the written data
        """
        configure_preset = ConfigurePreset(name='cppython', cacheVariables=None)
        presets = CMakePresets(configurePresets=[configure_preset])

        cppython_json_path = cppython_preset_directory / 'cppython.json'

        serialized = json.loads(presets.model_dump_json(exclude_none=True, by_alias=False))
        with open(cppython_json_path, 'w', encoding='utf8') as file:
            json.dump(serialized, file, ensure_ascii=False, indent=4)

        return cppython_json_path

    @staticmethod
    def write_root_presets(preset_file: Path, _: Path) -> None:
        """Read the top level json file and insert the include reference.

        Receives a relative path to the tool cmake json file

        Raises:
            ConfigError: If key files do not exists

        Args:
            preset_file: Preset file to modify
        """
        with open(preset_file, encoding='utf-8') as file:
            initial_root_preset = json.load(file)

        if (root_preset := deepcopy(initial_root_preset)) != initial_root_preset:
            with open(preset_file, 'w', encoding='utf-8') as file:
                json.dump(root_preset, file, ensure_ascii=False, indent=4)
