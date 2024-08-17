"""The vcpkg provider implementation
"""

import json
from logging import getLogger
from os import name as system_name
from pathlib import Path, PosixPath, WindowsPath
from typing import Any

from cppython_cmake.plugin import CMakeGenerator
from cppython_cmake.schema import CMakeSyncData
from cppython_core.exceptions import NotSupportedError, ProcessError
from cppython_core.plugin_schema.generator import SyncConsumer
from cppython_core.plugin_schema.provider import (
    Provider,
    ProviderPluginGroupData,
    SupportedProviderFeatures,
)
from cppython_core.schema import CorePluginData, Information, PluginName, SyncData
from cppython_core.utility import subprocess_call

from cppython_vcpkg.resolution import generate_manifest, resolve_vcpkg_data
from cppython_vcpkg.schema import VcpkgData


class VcpkgProvider(Provider):
    """vcpkg Provider"""

    def __init__(
        self, group_data: ProviderPluginGroupData, core_data: CorePluginData, configuration_data: dict[str, Any]
    ) -> None:
        self.group_data: ProviderPluginGroupData = group_data
        self.core_data: CorePluginData = core_data
        self.data: VcpkgData = resolve_vcpkg_data(configuration_data, core_data)

    @staticmethod
    def features(directory: Path) -> SupportedProviderFeatures:
        """Queries vcpkg support

        Args:
            directory: The directory to query

        Returns:
            Supported features
        """
        return SupportedProviderFeatures()

    @staticmethod
    def supported_sync_type(sync_type: type[SyncData]) -> bool:
        """_summary_

        Args:
            sync_type: _description_

        Returns:
            _description_
        """

        return sync_type in CMakeGenerator.sync_types()

    @staticmethod
    def information() -> Information:
        """Returns plugin information

        Returns:
            Plugin information
        """
        return Information()

    @classmethod
    def _update_provider(cls, path: Path) -> None:
        """Calls the vcpkg tool install script

        Args:
            path: The path where the script is located
        """

        logger = getLogger("cppython.vcpkg")

        try:
            if system_name == "nt":
                subprocess_call([str(WindowsPath("bootstrap-vcpkg.bat"))], logger=logger, cwd=path, shell=True)
            elif system_name == "posix":
                subprocess_call(["./" + str(PosixPath("bootstrap-vcpkg.sh"))], logger=logger, cwd=path, shell=True)
        except ProcessError:
            logger.error("Unable to bootstrap the vcpkg repository", exc_info=True)
            raise

    def sync_data(self, consumer: SyncConsumer) -> SyncData:
        """Gathers a data object for the given generator

        Args:
            consumer: The input consumer

        Raises:
            NotSupportedError: If not supported

        Returns:
            The synch data object
        """

        for sync_type in consumer.sync_types():
            if sync_type == CMakeSyncData:
                toolchain_file = self.core_data.cppython_data.install_path / "scripts/buildsystems/vcpkg.cmake"
                return CMakeSyncData(provider_name=PluginName("vcpkg"), toolchain=toolchain_file)

        raise NotSupportedError("OOF")

    @classmethod
    def tooling_downloaded(cls, path: Path) -> bool:
        """Returns whether the provider tooling needs to be downloaded

        Args:
            path: The directory to check for downloaded tooling

        Raises:
            ProcessError: Failed vcpkg calls

        Returns:
            Whether the tooling has been downloaded or not
        """

        logger = getLogger("cppython.vcpkg")

        try:
            # Hide output, given an error output is a logic conditional
            subprocess_call(
                ["git", "rev-parse", "--is-inside-work-tree"],
                logger=logger,
                suppress=True,
                cwd=path,
            )

        except ProcessError:
            return False

        return True

    @classmethod
    async def download_tooling(cls, directory: Path) -> None:
        """Installs the external tooling required by the provider

        Args:
            directory: The directory to download any extra tooling to

        Raises:
            ProcessError: Failed vcpkg calls
        """
        logger = getLogger("cppython.vcpkg")

        if cls.tooling_downloaded(directory):
            try:
                # The entire history is need for vcpkg 'baseline' information
                subprocess_call(["git", "fetch", "origin"], logger=logger, cwd=directory)
                subprocess_call(["git", "pull"], logger=logger, cwd=directory)
            except ProcessError:
                logger.exception("Unable to update the vcpkg repository")
                raise
        else:
            try:
                # The entire history is need for vcpkg 'baseline' information
                subprocess_call(
                    ["git", "clone", "https://github.com/microsoft/vcpkg", "."],
                    logger=logger,
                    cwd=directory,
                )

            except ProcessError:
                logger.exception("Unable to clone the vcpkg repository")
                raise

        cls._update_provider(directory)

    def install(self) -> None:
        """Called when dependencies need to be installed from a lock file.

        Raises:
            ProcessError: Failed vcpkg calls
        """

        manifest_directory = self.core_data.project_data.pyproject_file.parent
        manifest = generate_manifest(self.core_data, self.data)

        # Write out the manifest
        serialized = json.loads(manifest.json(exclude_none=True, by_alias=True))
        with open(manifest_directory / "vcpkg.json", "w", encoding="utf8") as file:
            json.dump(serialized, file, ensure_ascii=False, indent=4)

        executable = self.core_data.cppython_data.install_path / "vcpkg"
        logger = getLogger("cppython.vcpkg")
        try:
            subprocess_call(
                [
                    executable,
                    "install",
                    f"--x-install-root={self.data.install_directory}",
                ],
                logger=logger,
                cwd=self.core_data.cppython_data.build_path,
            )
        except ProcessError:
            logger.exception("Unable to install project dependencies")
            raise

    def update(self) -> None:
        """Called when dependencies need to be updated and written to the lock file.

        Raises:
            ProcessError: Failed vcpkg calls
        """
        manifest_directory = self.core_data.project_data.pyproject_file.parent
        manifest = generate_manifest(self.core_data, self.data)

        # Write out the manifest
        serialized = json.loads(manifest.json(exclude_none=True, by_alias=True))
        with open(manifest_directory / "vcpkg.json", "w", encoding="utf8") as file:
            json.dump(serialized, file, ensure_ascii=False, indent=4)

        executable = self.core_data.cppython_data.install_path / "vcpkg"
        logger = getLogger("cppython.vcpkg")
        try:
            subprocess_call(
                [
                    executable,
                    "install",
                    f"--x-install-root={self.data.install_directory}",
                ],
                logger=logger,
                cwd=self.core_data.cppython_data.build_path,
            )
        except ProcessError:
            logger.exception("Unable to install project dependencies")
            raise
