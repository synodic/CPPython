"""The Meson generator implementation"""

import subprocess
from pathlib import Path
from typing import Any

from cppython.core.plugin_schema.generator import (
    Generator,
    GeneratorPluginGroupData,
    SupportedGeneratorFeatures,
)
from cppython.core.schema import CorePluginData, Information, SupportedFeatures, SyncData
from cppython.plugins.meson.builder import Builder
from cppython.plugins.meson.resolution import resolve_meson_data
from cppython.plugins.meson.schema import MesonSyncData


class MesonGenerator(Generator):
    """Meson generator"""

    def __init__(self, group_data: GeneratorPluginGroupData, core_data: CorePluginData, data: dict[str, Any]) -> None:
        """Initializes the generator."""
        self.group_data = group_data
        self.core_data = core_data
        self.data = resolve_meson_data(data, core_data)
        self.builder = Builder()

        self._cppython_meson_directory = self.core_data.cppython_data.tool_path / 'cppython' / 'meson'

        # Track injected native/cross files for use in meson setup
        self._native_file: Path | None = None
        self._cross_file: Path | None = None

    @staticmethod
    def features(directory: Path) -> SupportedFeatures:
        """Queries if Meson is supported.

        Args:
            directory: The root directory where features are evaluated

        Returns:
            The supported features
        """
        return SupportedGeneratorFeatures()

    @staticmethod
    def information() -> Information:
        """Queries plugin info.

        Returns:
            Plugin information
        """
        return Information()

    @staticmethod
    def sync_types() -> list[type[SyncData]]:
        """Returns types in order of preference.

        Returns:
            The available types
        """
        return [MesonSyncData]

    def sync(self, sync_data: SyncData) -> None:
        """Disk sync point.

        Receives sync data from the provider and writes native/cross files
        that will be passed to ``meson setup``.

        Args:
            sync_data: The input data
        """
        match sync_data:
            case MesonSyncData():
                project_root = self.core_data.project_data.project_root

                self._native_file = self.builder.write_native_file(
                    self._cppython_meson_directory, sync_data, project_root
                )
                self._cross_file = self.builder.write_cross_file(
                    self._cppython_meson_directory, sync_data, project_root
                )
            case _:
                raise ValueError('Unsupported sync data type')

    def _meson_command(self) -> str:
        """Returns the meson command to use.

        Returns:
            The meson binary path as a string
        """
        if self.data.meson_binary:
            return str(self.data.meson_binary)
        return 'meson'

    def _build_dir(self) -> Path:
        """Returns the absolute path to the meson build directory.

        Returns:
            The build directory path
        """
        return self.data.build_file.parent / self.data.build_directory

    def _ensure_setup(self) -> None:
        """Ensure the meson build directory is configured.

        Runs ``meson setup`` if the build directory doesn't exist yet,
        or ``meson setup --reconfigure`` if it does.
        """
        build_dir = self._build_dir()
        source_dir = self.data.build_file.parent

        cmd = [self._meson_command(), 'setup']

        # Add native file if available
        if self._native_file and self._native_file.exists():
            cmd.extend(['--native-file', str(self._native_file)])

        # Add cross file if available
        if self._cross_file and self._cross_file.exists():
            cmd.extend(['--cross-file', str(self._cross_file)])

        if build_dir.exists():
            cmd.append('--reconfigure')

        cmd.extend([str(build_dir), str(source_dir)])

        subprocess.run(cmd, check=True, cwd=source_dir)

    def _effective_build_dir(self, configuration: str | None) -> Path:
        """Returns the build directory, optionally overridden by a configuration name.

        Args:
            configuration: If provided, used as the build directory name instead of the
                configured ``build_directory``.

        Returns:
            The absolute path to the build directory
        """
        directory = configuration if configuration else self.data.build_directory
        return self.data.build_file.parent / directory

    def build(self, configuration: str | None = None) -> None:
        """Builds the project using meson compile.

        Args:
            configuration: Optional build directory name override.
        """
        self._ensure_setup()
        build_dir = self._effective_build_dir(configuration)
        cmd = [self._meson_command(), 'compile', '-C', str(build_dir)]
        subprocess.run(cmd, check=True, cwd=self.data.build_file.parent)

    def test(self, configuration: str | None = None) -> None:
        """Runs tests using meson test.

        Args:
            configuration: Optional build directory name override.
        """
        build_dir = self._effective_build_dir(configuration)
        cmd = [self._meson_command(), 'test', '-C', str(build_dir)]
        subprocess.run(cmd, check=True, cwd=self.data.build_file.parent)

    def bench(self, configuration: str | None = None) -> None:
        """Runs benchmarks using meson test --benchmark.

        Args:
            configuration: Optional build directory name override.
        """
        build_dir = self._effective_build_dir(configuration)
        cmd = [self._meson_command(), 'test', '--benchmark', '-C', str(build_dir)]
        subprocess.run(cmd, check=True, cwd=self.data.build_file.parent)

    def run(self, target: str, configuration: str | None = None) -> None:
        """Runs a built executable by target name.

        Searches the build directory for the executable matching the target name.

        Args:
            target: The name of the build target/executable to run
            configuration: Optional build directory name override.

        Raises:
            FileNotFoundError: If the target executable cannot be found
        """
        build_dir = self._effective_build_dir(configuration)

        # Search for the executable in the build directory
        candidates = list(build_dir.rglob(target)) + list(build_dir.rglob(f'{target}.exe'))
        executables = [c for c in candidates if c.is_file()]

        if not executables:
            raise FileNotFoundError(f"Could not find executable '{target}' in build directory: {build_dir}")

        executable = executables[0]
        subprocess.run([str(executable)], check=True, cwd=self.data.build_file.parent)

    def list_targets(self) -> list[str]:
        """Lists discovered build targets/executables in the Meson build directory.

        Searches the build directory for executable files.

        Returns:
            A sorted list of unique target names found.
        """
        build_dir = self._build_dir()

        if not build_dir.exists():
            return []

        targets: set[str] = set()
        for candidate in build_dir.rglob('*'):
            if candidate.is_file() and (candidate.stat().st_mode & 0o111 or candidate.suffix == '.exe'):
                targets.add(candidate.stem)

        return sorted(targets)
