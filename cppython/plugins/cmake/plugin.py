"""The CMake generator implementation"""

import subprocess
from pathlib import Path
from typing import Any

from cppython.core.plugin_schema.generator import (
    Generator,
    GeneratorPluginGroupData,
    SupportedGeneratorFeatures,
)
from cppython.core.schema import CorePluginData, Information, PluginReport, SupportedFeatures, SyncData
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

    def _resolve_configuration(self, configuration: str | None) -> str:
        """Resolves the effective CMake preset from CLI argument or default config.

        Args:
            configuration: The configuration value passed from the CLI, or None

        Returns:
            The resolved CMake preset name

        Raises:
            ValueError: If no configuration is available from either CLI or default-configuration config
        """
        effective = configuration or self.data.default_configuration
        if effective is None:
            raise ValueError(
                'CMake generator requires a configuration. '
                "Provide --configuration on the CLI or set 'default-configuration' in [tool.cppython.generators.cmake]."
            )
        return effective

    def build(self, configuration: str | None = None) -> None:
        """Builds the project using cmake --build with the resolved preset.

        Args:
            configuration: Optional CMake preset name. Overrides default-configuration from config.
        """
        preset = self._resolve_configuration(configuration)
        cmd = [self._cmake_command(), '--build', '--preset', preset]
        subprocess.run(cmd, check=True, cwd=self.data.preset_file.parent)

    def test(self, configuration: str | None = None) -> None:
        """Runs tests using ctest with the resolved preset.

        Args:
            configuration: Optional CMake preset name. Overrides default-configuration from config.
        """
        preset = self._resolve_configuration(configuration)
        cmd = [self._ctest_command(), '--preset', preset]
        subprocess.run(cmd, check=True, cwd=self.data.preset_file.parent)

    def bench(self, configuration: str | None = None) -> None:
        """Runs benchmarks using ctest with the resolved preset.

        Args:
            configuration: Optional CMake preset name. Overrides default-configuration from config.
        """
        preset = self._resolve_configuration(configuration)
        cmd = [self._ctest_command(), '--preset', preset]
        subprocess.run(cmd, check=True, cwd=self.data.preset_file.parent)

    def run(self, target: str, configuration: str | None = None) -> None:
        """Runs a built executable by target name.

        Searches the build directory for the executable matching the target name.

        Args:
            target: The name of the build target/executable to run
            configuration: Optional CMake preset name. Overrides default-configuration from config.

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

    def list_targets(self) -> list[str]:
        """Lists discovered build targets/executables in the CMake build directory.

        Searches the build directory for executable files, excluding common
        non-target files.

        Returns:
            A sorted list of unique target names found.
        """
        build_path = self.core_data.cppython_data.build_path

        if not build_path.exists():
            return []

        # Collect executable files from the build directory
        targets: set[str] = set()
        for candidate in build_path.rglob('*'):
            if candidate.is_file() and (candidate.stat().st_mode & 0o111 or candidate.suffix == '.exe'):
                # Use the stem (name without extension) as the target name
                targets.add(candidate.stem)

        return sorted(targets)

    def plugin_info(self) -> PluginReport:
        """Return a report describing the CMake generator's configuration and managed files.

        Returns:
            A :class:`PluginReport` with CMake-specific details.
        """
        managed = [self._cppython_preset_directory / 'CPPython.json']

        config: dict[str, object] = {
            'preset_file': str(self.data.preset_file),
            'configuration_name': self.data.configuration_name,
        }
        if self.data.cmake_binary is not None:
            config['cmake_binary'] = str(self.data.cmake_binary)
        if self.data.default_configuration is not None:
            config['default_configuration'] = self.data.default_configuration

        return PluginReport(
            configuration=config,
            managed_files=managed,
        )
