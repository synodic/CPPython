"""Conan Provider Plugin

This module implements the Conan provider plugin for CPPython. It handles
integration with the Conan package manager, including dependency resolution,
installation, and synchronization with other tools.
"""

import os
from logging import Logger, getLogger
from pathlib import Path
from typing import Any

from conan.api.conan_api import ConanAPI
from conan.cli.cli import Cli

from cppython.core.plugin_schema.generator import SyncConsumer
from cppython.core.plugin_schema.provider import Provider, ProviderPluginGroupData, SupportedProviderFeatures
from cppython.core.schema import CorePluginData, Information, SupportedFeatures, SyncData
from cppython.plugins.cmake.plugin import CMakeGenerator
from cppython.plugins.cmake.schema import CMakeSyncData
from cppython.plugins.conan.builder import Builder
from cppython.plugins.conan.resolution import resolve_conan_data, resolve_conan_dependency
from cppython.plugins.conan.schema import ConanData
from cppython.utility.exception import NotSupportedError, ProviderInstallationError
from cppython.utility.utility import TypeName


class ConanProvider(Provider):
    """Conan Provider"""

    def __init__(
        self, group_data: ProviderPluginGroupData, core_data: CorePluginData, configuration_data: dict[str, Any]
    ) -> None:
        """Initializes the provider"""
        self.group_data: ProviderPluginGroupData = group_data
        self.core_data: CorePluginData = core_data
        self.data: ConanData = resolve_conan_data(configuration_data, core_data)

        self.builder = Builder()
        # Initialize ConanAPI once and reuse it
        self._conan_api = ConanAPI()
        # Initialize CLI for command API to work properly
        self._cli = Cli(self._conan_api)
        self._cli.add_commands()

        self._ensure_default_profiles()

    @staticmethod
    def features(directory: Path) -> SupportedFeatures:
        """Queries conan support

        Args:
            directory: The directory to query

        Returns:
            Supported features - `SupportedProviderFeatures`. Cast to this type to help us avoid generic typing
        """
        return SupportedProviderFeatures()

    @staticmethod
    def information() -> Information:
        """Returns plugin information

        Returns:
            Plugin information
        """
        return Information()

    def _install_dependencies(self, *, update: bool = False) -> None:
        """Install/update dependencies using Conan CLI.

        Args:
            update: If True, check remotes for newer versions/revisions and install those.
                   If False, use cached versions when available.
        """
        operation = 'update' if update else 'install'
        logger = getLogger('cppython.conan')

        try:
            # Setup environment and generate conanfile
            conanfile_path = self._prepare_installation()
        except Exception as e:
            raise ProviderInstallationError('conan', f'Failed to prepare {operation} environment: {e}', e) from e

        try:
            build_types = ['Release', 'Debug']
            for build_type in build_types:
                logger.info('Installing dependencies for build type: %s', build_type)
                self._run_conan_install(conanfile_path, update, build_type, logger)
        except Exception as e:
            raise ProviderInstallationError('conan', f'Failed to install dependencies: {e}', e) from e

    def _prepare_installation(self) -> Path:
        """Prepare the installation environment and generate conanfile.

        Returns:
            Path to conanfile.py
        """
        # Resolve dependencies and generate conanfile.py
        resolved_dependencies = [resolve_conan_dependency(req) for req in self.core_data.cppython_data.dependencies]
        self.builder.generate_conanfile(
            self.core_data.project_data.project_root,
            resolved_dependencies,
            self.core_data.pep621_data.name,
            self.core_data.pep621_data.version,
        )

        # Ensure build directory exists
        self.core_data.cppython_data.build_path.mkdir(parents=True, exist_ok=True)

        # Setup paths
        project_root = self.core_data.project_data.project_root
        conanfile_path = project_root / 'conanfile.py'

        if not conanfile_path.exists():
            raise FileNotFoundError('Generated conanfile.py not found')

        return conanfile_path

    def _ensure_default_profiles(self) -> None:
        """Ensure default Conan profiles exist, creating them if necessary."""
        try:
            self._conan_api.profiles.get_default_host()
            self._conan_api.profiles.get_default_build()
        except Exception:
            # If profiles don't exist, create them using profile detect
            self._conan_api.command.run(['profile', 'detect'])

    def _run_conan_install(self, conanfile_path: Path, update: bool, build_type: str, logger: Logger) -> None:
        """Run conan install command using Conan API with optional build type.

        Args:
            conanfile_path: Path to the conanfile.py
            update: Whether to check for updates
            build_type: Build type (Release, Debug, etc.) or None for default
            logger: Logger instance
        """
        # Build conan install command arguments
        command_args = ['install', str(conanfile_path)]

        # Add build missing flag
        command_args.extend(['--build', 'missing'])

        # Add update flag if needed
        if update:
            command_args.append('--update')

        # Add build type setting if specified
        if build_type:
            command_args.extend(['-s', f'build_type={build_type}'])

        # Log the command being executed
        logger.info('Executing conan command: conan %s', ' '.join(command_args))

        try:
            # Use reusable Conan API instance instead of subprocess
            # Change to project directory since Conan API might not handle cwd like subprocess
            original_cwd = os.getcwd()
            try:
                os.chdir(str(self.core_data.project_data.project_root))
                self._conan_api.command.run(command_args)
            finally:
                os.chdir(original_cwd)
        except Exception as e:
            error_msg = str(e)
            logger.error('Conan install failed: %s', error_msg, exc_info=True)
            raise ProviderInstallationError('conan', error_msg, e) from e

    def install(self) -> None:
        """Installs the provider"""
        self._install_dependencies(update=False)

    def update(self) -> None:
        """Updates the provider"""
        self._install_dependencies(update=True)

    @staticmethod
    def supported_sync_type(sync_type: type[SyncData]) -> bool:
        """Checks if the given sync type is supported by the Conan provider.

        Args:
            sync_type: The type of synchronization data to check.

        Returns:
            True if the sync type is supported, False otherwise.
        """
        return sync_type in CMakeGenerator.sync_types()

    def sync_data(self, consumer: SyncConsumer) -> SyncData:
        """Generates synchronization data for the given consumer.

        Args:
            consumer: The input consumer for which synchronization data is generated.

        Returns:
            The synchronization data object.

        Raises:
            NotSupportedError: If the consumer's sync type is not supported.
        """
        for sync_type in consumer.sync_types():
            if sync_type == CMakeSyncData:
                return self._create_cmake_sync_data()

        raise NotSupportedError(f'Unsupported sync types: {consumer.sync_types()}')

    def _create_cmake_sync_data(self) -> CMakeSyncData:
        """Creates CMake synchronization data with Conan toolchain configuration.

        Returns:
            CMakeSyncData configured for Conan integration
        """
        conan_toolchain_path = self.core_data.cppython_data.build_path / 'generators' / 'conan_toolchain.cmake'

        return CMakeSyncData(
            provider_name=TypeName('conan'),
            toolchain_file=conan_toolchain_path,
        )

    @classmethod
    async def download_tooling(cls, directory: Path) -> None:
        """Download external tooling required by the Conan provider.

        Since we're using CMakeToolchain generator instead of cmake-conan provider,
        no external tooling needs to be downloaded.
        """
        # No external tooling required when using CMakeToolchain
        pass

    def publish(self) -> None:
        """Publishes the package using conan create workflow."""
        project_root = self.core_data.project_data.project_root
        conanfile_path = project_root / 'conanfile.py'
        logger = getLogger('cppython.conan')

        if not conanfile_path.exists():
            raise FileNotFoundError(f'conanfile.py not found at {conanfile_path}')

        try:
            # Build conan create command arguments
            command_args = ['create', str(conanfile_path)]

            # Add build mode (build everything for publishing)
            command_args.extend(['--build', 'missing'])

            # Log the command being executed
            logger.info('Executing conan create command: conan %s', ' '.join(command_args))

            # Run conan create using reusable Conan API instance
            # Change to project directory since Conan API might not handle cwd like subprocess
            original_cwd = os.getcwd()
            try:
                os.chdir(str(project_root))
                self._conan_api.command.run(command_args)
            finally:
                os.chdir(original_cwd)

            # Upload if not skipped
            if not self.data.skip_upload:
                self._upload_package(logger)

        except Exception as e:
            error_msg = str(e)
            logger.error('Conan create failed: %s', error_msg, exc_info=True)
            raise ProviderInstallationError('conan', error_msg, e) from e

    def _upload_package(self, logger) -> None:
        """Upload the package to configured remotes using Conan API."""
        # If no remotes configured, upload to all remotes
        if not self.data.remotes:
            # Upload to all available remotes
            command_args = ['upload', '*', '--all', '--confirm']
        else:
            # Upload only to specified remotes
            for remote in self.data.remotes:
                command_args = ['upload', '*', '--remote', remote, '--all', '--confirm']

                # Log the command being executed
                logger.info('Executing conan upload command: conan %s', ' '.join(command_args))

                try:
                    self._conan_api.command.run(command_args)
                except Exception as e:
                    error_msg = str(e)
                    logger.error('Conan upload failed for remote %s: %s', remote, error_msg, exc_info=True)
                    raise ProviderInstallationError('conan', f'Upload to {remote} failed: {error_msg}', e) from e
            return

        # Log the command for uploading to all remotes
        logger.info('Executing conan upload command: conan %s', ' '.join(command_args))

        try:
            self._conan_api.command.run(command_args)
        except Exception as e:
            error_msg = str(e)
            logger.error('Conan upload failed: %s', error_msg, exc_info=True)
            raise ProviderInstallationError('conan', error_msg, e) from e
