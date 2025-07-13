"""Conan Provider Plugin

This module implements the Conan provider plugin for CPPython. It handles
integration with the Conan package manager, including dependency resolution,
installation, and synchronization with other tools.
"""

import logging
import subprocess
from pathlib import Path
from typing import Any

import requests
from conan.api.conan_api import ConanAPI
from conan.api.model import ListPattern

from cppython.core.plugin_schema.generator import SyncConsumer
from cppython.core.plugin_schema.provider import Provider, ProviderPluginGroupData, SupportedProviderFeatures
from cppython.core.schema import CorePluginData, Information, SupportedFeatures, SyncData
from cppython.plugins.cmake.plugin import CMakeGenerator
from cppython.plugins.cmake.schema import CMakeSyncData
from cppython.plugins.conan.builder import Builder
from cppython.plugins.conan.resolution import resolve_conan_data, resolve_conan_dependency
from cppython.plugins.conan.schema import ConanData
from cppython.utility.exception import NotSupportedError, ProviderConfigurationError, ProviderInstallationError
from cppython.utility.utility import TypeName


class ConanProvider(Provider):
    """Conan Provider"""

    _provider_url = 'https://raw.githubusercontent.com/conan-io/cmake-conan/refs/heads/develop2/conan_provider.cmake'

    def __init__(
        self, group_data: ProviderPluginGroupData, core_data: CorePluginData, configuration_data: dict[str, Any]
    ) -> None:
        """Initializes the provider"""
        self.group_data: ProviderPluginGroupData = group_data
        self.core_data: CorePluginData = core_data
        self.data: ConanData = resolve_conan_data(configuration_data, core_data)

        self.builder = Builder()

    @staticmethod
    def _download_file(url: str, file: Path) -> None:
        """Replaces the given file with the contents of the url"""
        file.parent.mkdir(parents=True, exist_ok=True)

        with open(file, 'wb') as out_file:
            content = requests.get(url, stream=True).content
            out_file.write(content)

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
        """Install/update dependencies using conan CLI command.

        Args:
            update: If True, check remotes for newer versions/revisions and install those.
                   If False, use cached versions when available.
        """
        try:
            logger = logging.getLogger('cppython.conan')
            logger.debug('Starting dependency installation/update (update=%s)', update)

            resolved_dependencies = [resolve_conan_dependency(req) for req in self.core_data.cppython_data.dependencies]
            logger.debug(
                'Resolved %d dependencies: %s', len(resolved_dependencies), [str(dep) for dep in resolved_dependencies]
            )

            # Generate conanfile.py
            self.builder.generate_conanfile(self.core_data.project_data.project_root, resolved_dependencies)
            logger.debug('Generated conanfile.py at %s', self.core_data.project_data.project_root)

            # Ensure build directory exists
            self.core_data.cppython_data.build_path.mkdir(parents=True, exist_ok=True)
            logger.debug('Created build path: %s', self.core_data.cppython_data.build_path)

            # Build conan install command
            project_root = self.core_data.project_data.project_root
            conanfile_path = project_root / 'conanfile.py'

            if not conanfile_path.exists():
                raise ProviderInstallationError('conan', 'Generated conanfile.py not found')

            # Prepare conan install command
            cmd = [
                'conan',
                'install',
                str(conanfile_path),
                '--output-folder',
                str(self.core_data.cppython_data.build_path),
                '--build',
                'missing',
            ]

            if update:
                cmd.extend(['--update'])

            logger.debug('Running conan command: %s', ' '.join(cmd))

            # Execute conan install command
            result = subprocess.run(cmd, cwd=str(project_root), capture_output=True, text=True, check=False)

            # Log output for debugging
            if result.stdout:
                logger.debug('Conan stdout:\n%s', result.stdout)
            if result.stderr:
                logger.debug('Conan stderr:\n%s', result.stderr)

            # Check for success
            if result.returncode != 0:
                error_msg = f'Conan install failed with return code {result.returncode}'
                if result.stderr:
                    error_msg += f': {result.stderr}'
                raise ProviderInstallationError('conan', error_msg)

            logger.debug('Successfully installed dependencies using conan CLI')

        except subprocess.SubprocessError as e:
            operation = 'update' if update else 'install'
            raise ProviderInstallationError('conan', f'Failed to {operation} dependencies: {e}', e) from e
        except Exception as e:
            operation = 'update' if update else 'install'
            error_msg = str(e)
            raise ProviderInstallationError('conan', f'Failed to {operation} dependencies: {error_msg}', e) from e

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
                return CMakeSyncData(
                    provider_name=TypeName('conan'),
                    top_level_includes=self.core_data.cppython_data.install_path / 'conan_provider.cmake',
                )

        raise NotSupportedError('OOF')

    @classmethod
    async def download_tooling(cls, directory: Path) -> None:
        """Downloads the conan provider file"""
        cls._download_file(cls._provider_url, directory / 'conan_provider.cmake')

    def publish(self) -> None:
        """Publishes the package using conan create workflow."""
        # Get the project root directory where conanfile.py should be located
        project_root = self.core_data.project_data.project_root
        conanfile_path = project_root / 'conanfile.py'

        if not conanfile_path.exists():
            raise FileNotFoundError(f'conanfile.py not found at {conanfile_path}')

        # Initialize Conan API
        conan_api = ConanAPI()

        # Get configured remotes from Conan API and filter by our configuration
        # TODO: We want to replace the global conan remotes with the ones configured in CPPython.
        all_remotes = conan_api.remotes.list()
        if not self.data.local_only:
            # Filter remotes to only include those specified in configuration
            configured_remotes = [remote for remote in all_remotes if remote.name in self.data.remotes]

            if not configured_remotes:
                available_remotes = [remote.name for remote in all_remotes]
                raise ProviderConfigurationError(
                    'conan',
                    f'No configured remotes found. Available remotes: {available_remotes}, '
                    f'Configured remotes: {self.data.remotes}',
                    'remotes',
                )
        else:
            configured_remotes = []

        # Step 1: Export the recipe to the cache
        # This is equivalent to the export part of `conan create`
        ref, conanfile = conan_api.export.export(
            path=str(conanfile_path),
            name=None,
            version=None,
            user=None,
            channel=None,
            lockfile=None,
            remotes=all_remotes,  # Use all remotes for dependency resolution during export
        )

        # Step 2: Get default profiles
        profile_host_path = conan_api.profiles.get_default_host()
        profile_build_path = conan_api.profiles.get_default_build()
        profile_host = conan_api.profiles.get_profile([profile_host_path])
        profile_build = conan_api.profiles.get_profile([profile_build_path])

        # Step 3: Build dependency graph for the package
        deps_graph = conan_api.graph.load_graph_consumer(
            path=str(conanfile_path),
            name=None,
            version=None,
            user=None,
            channel=None,
            profile_host=profile_host,
            profile_build=profile_build,
            lockfile=None,
            remotes=all_remotes,  # Use all remotes for dependency resolution
            update=None,
            check_updates=False,
            is_build_require=False,
        )

        # Step 4: Analyze binaries and install/build them if needed
        conan_api.graph.analyze_binaries(
            graph=deps_graph,
            build_mode=['*'],  # Build from source (equivalent to the create behavior)
            remotes=all_remotes,  # Use all remotes for dependency resolution
            update=None,
            lockfile=None,
        )

        # Step 5: Install all dependencies and build the package
        conan_api.install.install_binaries(deps_graph=deps_graph, remotes=all_remotes)

        # If not local only, upload the package
        if not self.data.local_only:
            # Get all packages matching the created reference
            ref_pattern = ListPattern(f'{ref.name}/*', package_id='*', only_recipe=False)
            package_list = conan_api.list.select(ref_pattern)

            if package_list.recipes:
                # Use the first configured remote for upload
                remote = configured_remotes[0]

                # Upload the package to configured remotes
                conan_api.upload.upload_full(
                    package_list=package_list,
                    remote=remote,
                    enabled_remotes=configured_remotes,  # Only upload to configured remotes
                    check_integrity=False,
                    force=False,
                    metadata=None,
                    dry_run=False,
                )
            else:
                raise ProviderInstallationError('conan', 'No packages found to upload')
