"""The vcpkg provider implementation"""

import subprocess
from logging import getLogger
from os import name as system_name
from pathlib import Path, PosixPath, WindowsPath
from typing import Any

from cppython.core.plugin_schema.generator import SyncConsumer
from cppython.core.plugin_schema.provider import (
    Provider,
    ProviderPluginGroupData,
    SupportedProviderFeatures,
)
from cppython.core.schema import CorePluginData, Information, SupportedFeatures, SyncData
from cppython.plugins.cmake.plugin import CMakeGenerator
from cppython.plugins.cmake.schema import CMakeSyncData
from cppython.plugins.vcpkg.resolution import generate_manifest, resolve_vcpkg_data
from cppython.plugins.vcpkg.schema import VcpkgData
from cppython.utility.exception import NotSupportedError, ProviderInstallationError, ProviderToolingError
from cppython.utility.utility import TypeName


class VcpkgProvider(Provider):
    """vcpkg Provider"""

    def __init__(
        self, group_data: ProviderPluginGroupData, core_data: CorePluginData, configuration_data: dict[str, Any]
    ) -> None:
        """Initializes the provider"""
        self.group_data: ProviderPluginGroupData = group_data
        self.core_data: CorePluginData = core_data
        self.data: VcpkgData = resolve_vcpkg_data(configuration_data, core_data)

    @staticmethod
    def features(directory: Path) -> SupportedFeatures:
        """Queries vcpkg support

        Args:
            directory: The directory to query

        Returns:
            Supported features - `SupportedProviderFeatures`. Cast to this type to help us avoid generic typing
        """
        return SupportedProviderFeatures()

    @staticmethod
    def supported_sync_type(sync_type: type[SyncData]) -> bool:
        """Checks if the given sync type is supported by the vcpkg provider.

        Args:
            sync_type: The type of synchronization data to check.

        Returns:
            True if the sync type is supported, False otherwise.
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
        logger = getLogger('cppython.vcpkg')

        try:
            if system_name == 'nt':
                subprocess.run(
                    [str(WindowsPath('bootstrap-vcpkg.bat')), '-disableMetrics'],
                    cwd=path,
                    shell=True,
                    check=True,
                    capture_output=True,
                )
            elif system_name == 'posix':
                subprocess.run(
                    ['./' + str(PosixPath('bootstrap-vcpkg.sh')), '-disableMetrics'],
                    cwd=path,
                    shell=True,
                    check=True,
                    capture_output=True,
                )
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            logger.error('Unable to bootstrap the vcpkg repository: %s', error_msg, exc_info=True)
            raise ProviderToolingError('vcpkg', 'bootstrap', error_msg, e) from e

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
                return CMakeSyncData(
                    provider_name=TypeName('vcpkg'),
                    top_level_includes=self.core_data.cppython_data.install_path / 'scripts/buildsystems/vcpkg.cmake',
                )

        raise NotSupportedError('OOF')

    @classmethod
    def tooling_downloaded(cls, path: Path) -> bool:
        """Returns whether the provider tooling needs to be downloaded

        Args:
            path: The directory to check for downloaded tooling

        Returns:
            Whether the tooling has been downloaded or not
        """
        try:
            subprocess.run(
                ['git', 'rev-parse', '--is-inside-work-tree'],
                cwd=path,
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError:
            return False

        return True

    @classmethod
    async def download_tooling(cls, directory: Path) -> None:
        """Installs the external tooling required by the provider

        Args:
            directory: The directory to download any extra tooling to
        """
        logger = getLogger('cppython.vcpkg')

        if cls.tooling_downloaded(directory):
            try:
                logger.debug("Updating the vcpkg repository at '%s'", directory.absolute())

                # The entire history is need for vcpkg 'baseline' information
                subprocess.run(
                    ['git', 'fetch', 'origin'],
                    cwd=directory,
                    check=True,
                    capture_output=True,
                )
                subprocess.run(
                    ['git', 'pull'],
                    cwd=directory,
                    check=True,
                    capture_output=True,
                )
            except subprocess.CalledProcessError as e:
                error_msg = e.stderr.decode() if e.stderr else str(e)
                logger.error('Unable to update the vcpkg repository: %s', error_msg, exc_info=True)
                raise ProviderToolingError('vcpkg', 'update', error_msg, e) from e
        else:
            try:
                logger.debug("Cloning the vcpkg repository to '%s'", directory.absolute())

                # The entire history is need for vcpkg 'baseline' information
                subprocess.run(
                    ['git', 'clone', 'https://github.com/microsoft/vcpkg', '.'],
                    cwd=directory,
                    check=True,
                    capture_output=True,
                )

            except subprocess.CalledProcessError as e:
                error_msg = e.stderr.decode() if e.stderr else str(e)
                logger.error('Unable to clone the vcpkg repository: %s', error_msg, exc_info=True)
                raise ProviderToolingError('vcpkg', 'clone', error_msg, e) from e

        cls._update_provider(directory)

    def install(self) -> None:
        """Called when dependencies need to be installed from a lock file."""
        manifest_directory = self.core_data.project_data.project_root
        manifest = generate_manifest(self.core_data, self.data)

        # Write out the manifest
        serialized = manifest.model_dump_json(exclude_none=True, by_alias=True, indent=4)
        with open(manifest_directory / 'vcpkg.json', 'w', encoding='utf8') as file:
            file.write(serialized)

        executable = self.core_data.cppython_data.install_path / 'vcpkg'
        install_directory = self.data.install_directory
        build_path = self.core_data.cppython_data.build_path

        logger = getLogger('cppython.vcpkg')
        try:
            subprocess.run(
                [str(executable), 'install', f'--x-install-root={str(install_directory)}'],
                cwd=str(build_path),
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            logger.error('Unable to install project dependencies: %s', error_msg, exc_info=True)
            raise ProviderInstallationError('vcpkg', error_msg, e) from e

    def update(self) -> None:
        """Called when dependencies need to be updated and written to the lock file."""
        manifest_directory = self.core_data.project_data.project_root

        manifest = generate_manifest(self.core_data, self.data)

        # Write out the manifest
        serialized = manifest.model_dump_json(exclude_none=True, by_alias=True, indent=4)
        with open(manifest_directory / 'vcpkg.json', 'w', encoding='utf8') as file:
            file.write(serialized)

        executable = self.core_data.cppython_data.install_path / 'vcpkg'
        install_directory = self.data.install_directory
        build_path = self.core_data.cppython_data.build_path

        logger = getLogger('cppython.vcpkg')
        try:
            subprocess.run(
                [str(executable), 'install', f'--x-install-root={str(install_directory)}'],
                cwd=str(build_path),
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            logger.error('Unable to update project dependencies: %s', error_msg, exc_info=True)
            raise ProviderInstallationError('vcpkg', error_msg, e) from e

    def publish(self) -> None:
        """Called when the project needs to be published.

        Raises:
            NotImplementedError: vcpkg does not support publishing
        """
        raise NotImplementedError('vcpkg does not support publishing')
