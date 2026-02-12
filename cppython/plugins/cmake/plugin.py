"""The CMake generator implementation"""

import subprocess
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

                cppython_preset_file = self._cppython_preset_directory / 'CPPython.json'

                project_root = self.core_data.project_data.project_root

                cppython_preset_file = self.builder.write_cppython_preset(
                    self._cppython_preset_directory, cppython_preset_file, sync_data, project_root
                )

                self.builder.write_root_presets(
                    self.data.preset_file, cppython_preset_file, self.data, self.core_data.cppython_data.build_path
                )
            case _:
                raise ValueError('Unsupported sync data type')

    def _cmake_command(self) -> str:
        """Returns the cmake command to use.

        Returns:
            The cmake binary path as a string
        """
        if self.data.cmake_binary:
            return str(self.data.cmake_binary)
        return 'cmake'

    def _ctest_command(self) -> str:
        """Returns the ctest command to use.

        Derives the ctest path from the cmake binary path when available.

        Returns:
            The ctest binary path as a string
        """
        if self.data.cmake_binary:
            # ctest is typically in the same directory as cmake
            ctest_path = self.data.cmake_binary.parent / 'ctest'
            if ctest_path.exists():
                return str(ctest_path)
            # Try with .exe on Windows
            ctest_exe = self.data.cmake_binary.parent / 'ctest.exe'
            if ctest_exe.exists():
                return str(ctest_exe)
        return 'ctest'

    def build(self) -> None:
        """Builds the project using cmake --build with the configured preset."""
        release_preset = self.data.configuration_name + '-release'
        cmd = [self._cmake_command(), '--build', '--preset', release_preset]
        subprocess.run(cmd, check=True, cwd=self.data.preset_file.parent)

    def test(self) -> None:
        """Runs tests using ctest with the configured preset."""
        release_preset = self.data.configuration_name + '-release'
        cmd = [self._ctest_command(), '--preset', release_preset]
        subprocess.run(cmd, check=True, cwd=self.data.preset_file.parent)

    def bench(self) -> None:
        """Runs benchmarks using ctest with the configured benchmark preset."""
        bench_preset = self.data.configuration_name + '-bench-release'
        cmd = [self._ctest_command(), '--preset', bench_preset]
        subprocess.run(cmd, check=True, cwd=self.data.preset_file.parent)

    def run(self, target: str) -> None:
        """Runs a built executable by target name.

        Searches the build directory for the executable matching the target name.

        Args:
            target: The name of the build target/executable to run

        Raises:
            FileNotFoundError: If the target executable cannot be found
        """
        build_path = self.core_data.cppython_data.build_path

        # Search for the executable in the build directory
        candidates = list(build_path.rglob(target)) + list(build_path.rglob(f'{target}.exe'))
        executables = [c for c in candidates if c.is_file()]

        if not executables:
            raise FileNotFoundError(f"Could not find executable '{target}' in build directory: {build_path}")

        executable = executables[0]
        subprocess.run([str(executable)], check=True, cwd=self.data.preset_file.parent)
