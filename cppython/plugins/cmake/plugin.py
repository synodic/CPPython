"""The CMake generator implementation"""

from pathlib import Path
from typing import Any

from cppython.core.plugin_schema.generator import (
    Generator,
    GeneratorPluginGroupData,
    SupportedGeneratorFeatures,
)
from cppython.core.schema import CorePluginData, Information, SupportedFeatures, SyncData
from cppython.plugins.cmake.builder import Builder
from cppython.plugins.cmake.resolution import resolve_cmake_data
from cppython.plugins.cmake.schema import CMakeSyncData


class CMakeGenerator(Generator):
    """CMake generator"""

    def __init__(self, group_data: GeneratorPluginGroupData, core_data: CorePluginData, data: dict[str, Any]) -> None:
        """Initializes the generator"""
        self.group_data = group_data
        self.core_data = core_data
        self.data = resolve_cmake_data(data, core_data)
        self.builder = Builder()

        self._cppython_preset_directory = self.core_data.cppython_data.tool_path / 'cppython'
        self._provider_directory = self._cppython_preset_directory / 'providers'

    @staticmethod
    def features(directory: Path) -> SupportedFeatures:
        """Queries if CMake is supported

        Returns:
            The supported features - `SupportedGeneratorFeatures`. Cast to this type to help us avoid generic typing
        """
        return SupportedGeneratorFeatures()

    @staticmethod
    def information() -> Information:
        """Queries plugin info

        Returns:
            Plugin information
        """
        return Information()

    @staticmethod
    def sync_types() -> list[type[SyncData]]:
        """Returns types in order of preference

        Returns:
            The available types
        """
        return [CMakeSyncData]

    def sync(self, sync_data: SyncData) -> None:
        """Disk sync point

        Args:
            sync_data: The input data
        """
        match sync_data:
            case CMakeSyncData():
                self._cppython_preset_directory.mkdir(parents=True, exist_ok=True)
                self._provider_directory.mkdir(parents=True, exist_ok=True)

                self.builder.write_provider_preset(self._provider_directory, sync_data)

                cppython_preset_file = self.builder.write_cppython_preset(
                    self._cppython_preset_directory, self._provider_directory, sync_data
                )

                self.builder.write_root_presets(
                    self.data.preset_file, cppython_preset_file, self.data, self.core_data.cppython_data.build_path
                )
            case _:
                raise ValueError('Unsupported sync data type')
