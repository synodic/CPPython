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
from cppython.plugins.meson.plugin import MesonGenerator
from cppython.plugins.meson.schema import MesonSyncData
from cppython.plugins.vcpkg.resolution import generate_manifest, resolve_vcpkg_data
from cppython.plugins.vcpkg.schema import VcpkgData
from cppython.utility.exception import (
    InstallationVerificationError,
    NotSupportedError,
    ProviderInstallationError,
    ProviderToolingError,
)
from cppython.utility.subprocess import run_subprocess
from cppython.utility.utility import TypeName

logger = getLogger('cppython.vcpkg')


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
        return sync_type in CMakeGenerator.sync_types() or sync_type in MesonGenerator.sync_types()

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
        try:
            if system_name == 'nt':
                run_subprocess(
                    [str(WindowsPath('bootstrap-vcpkg.bat')), '-disableMetrics'],
                    cwd=path,
                    logger=logger,
                    shell=True,
                )
            elif system_name == 'posix':
                run_subprocess(
                    ['./' + str(PosixPath('bootstrap-vcpkg.sh')), '-disableMetrics'],
                    cwd=path,
                    logger=logger,
                    shell=True,
                )
        except subprocess.CalledProcessError as e:
            raise ProviderToolingError('vcpkg', 'bootstrap the vcpkg repository', str(e), e) from e

    def sync_data(self, consumer: SyncConsumer) -> SyncData:
        """Gathers a data object for the given generator.

        Args:
            consumer: The input consumer

        Raises:
            NotSupportedError: If not supported

        Returns:
            The sync data object
        """
        for sync_type in consumer.sync_types():
            if sync_type == CMakeSyncData:
                return self._create_cmake_sync_data()
            if sync_type == MesonSyncData:
                return self._create_meson_sync_data()

        raise NotSupportedError('OOF')

    def _create_cmake_sync_data(self) -> CMakeSyncData:
        """Creates CMake synchronization data with vcpkg configuration.

        Returns:
            CMakeSyncData configured for vcpkg integration
        """
        # Create CMakeSyncData with vcpkg configuration
        vcpkg_cmake_path = self.core_data.cppython_data.install_path / 'scripts/buildsystems/vcpkg.cmake'

        return CMakeSyncData(
            provider_name=TypeName('vcpkg'),
            toolchain_file=vcpkg_cmake_path,
        )

    def _create_meson_sync_data(self) -> MesonSyncData:
        """Creates Meson synchronization data with vcpkg configuration.

        vcpkg exposes installed dependencies via pkg-config. The native file
        points Meson's ``pkg_config_path`` to vcpkg's installed pkgconfig directory.

        Returns:
            MesonSyncData configured for vcpkg integration
        """
        # vcpkg installs pkg-config files under installed/<triplet>/lib/pkgconfig
        # We point Meson to the installed directory via a native file reference
        # The native file itself is generated by the Meson builder during sync
        vcpkg_pkgconfig_path = self.core_data.cppython_data.install_path / 'installed'

        # Create a native file path in the tool directory
        native_file = self.core_data.cppython_data.tool_path / 'cppython' / 'meson' / 'vcpkg_native.ini'

        # Write a minimal native file pointing to vcpkg's pkg-config
        native_file.parent.mkdir(parents=True, exist_ok=True)
        content = f"[built-in options]\npkg_config_path = '{vcpkg_pkgconfig_path.as_posix()}'\n"
        native_file.write_text(content, encoding='utf-8')

        return MesonSyncData(
            provider_name=TypeName('vcpkg'),
            native_file=native_file,
        )

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
        if cls.tooling_downloaded(directory):
            try:
                logger.debug("Updating the vcpkg repository at '%s'", directory.absolute())

                # The entire history is need for vcpkg 'baseline' information
                run_subprocess(
                    ['git', 'fetch', 'origin'],
                    cwd=directory,
                    logger=logger,
                )
                run_subprocess(
                    ['git', 'pull'],
                    cwd=directory,
                    logger=logger,
                )
            except subprocess.CalledProcessError as e:
                raise ProviderToolingError('vcpkg', 'update the vcpkg repository', str(e), e) from e
        else:
            try:
                logger.debug("Cloning the vcpkg repository to '%s'", directory.absolute())

                # The entire history is need for vcpkg 'baseline' information
                run_subprocess(
                    ['git', 'clone', 'https://github.com/microsoft/vcpkg', '.'],
                    cwd=directory,
                    logger=logger,
                )

            except subprocess.CalledProcessError as e:
                raise ProviderToolingError('vcpkg', 'clone the vcpkg repository', str(e), e) from e

        cls._update_provider(directory)

    def verify_installed(self) -> None:
        """Verify that vcpkg tooling and installed packages exist on disk.

        Checks that the vcpkg repository has been cloned and that the install
        directory contains packages from a prior ``install()`` call.

        Raises:
            InstallationVerificationError: If required artifacts are missing
        """
        missing: list[str] = []

        # Check that vcpkg tooling has been downloaded
        tooling_path = self.core_data.cppython_data.install_path
        if not self.tooling_downloaded(tooling_path):
            missing.append(f'vcpkg repository ({tooling_path})')

        # Check that packages have been installed
        install_directory = self.data.install_directory
        if not install_directory.is_dir() or not any(install_directory.iterdir()):
            missing.append(f'installed packages directory ({install_directory})')

        if missing:
            raise InstallationVerificationError('vcpkg', missing)

    def install(self, groups: list[str] | None = None) -> None:
        """Called when dependencies need to be installed from a lock file.

        Args:
            groups: Optional list of dependency group names to install (currently not used by vcpkg)
        """
        manifest_directory = self.core_data.project_data.project_root
        manifest = generate_manifest(self.core_data, self.data)

        # Write out the manifest
        serialized = manifest.model_dump_json(exclude_none=True, by_alias=True, indent=4)
        with open(manifest_directory / 'vcpkg.json', 'w', encoding='utf8') as file:
            file.write(serialized)

        executable = self.core_data.cppython_data.install_path / 'vcpkg'
        install_directory = self.data.install_directory
        build_path = self.core_data.cppython_data.build_path

        try:
            run_subprocess(
                [str(executable), 'install', f'--x-install-root={str(install_directory)}'],
                cwd=str(build_path),
                logger=logger,
            )
        except subprocess.CalledProcessError as e:
            raise ProviderInstallationError('vcpkg', f'install project dependencies: {e}', e) from e

    def update(self, groups: list[str] | None = None) -> None:
        """Called when dependencies need to be updated and written to the lock file.

        Args:
            groups: Optional list of dependency group names to update (currently not used by vcpkg)
        """
        manifest_directory = self.core_data.project_data.project_root

        manifest = generate_manifest(self.core_data, self.data)

        # Write out the manifest
        serialized = manifest.model_dump_json(exclude_none=True, by_alias=True, indent=4)
        with open(manifest_directory / 'vcpkg.json', 'w', encoding='utf8') as file:
            file.write(serialized)

        executable = self.core_data.cppython_data.install_path / 'vcpkg'
        install_directory = self.data.install_directory
        build_path = self.core_data.cppython_data.build_path

        try:
            run_subprocess(
                [str(executable), 'install', f'--x-install-root={str(install_directory)}'],
                cwd=str(build_path),
                logger=logger,
            )
        except subprocess.CalledProcessError as e:
            raise ProviderInstallationError('vcpkg', f'update project dependencies: {e}', e) from e

    def publish(self) -> None:
        """Called when the project needs to be published.

        Raises:
            NotImplementedError: vcpkg does not support publishing
        """
        raise NotImplementedError('vcpkg does not support publishing')
