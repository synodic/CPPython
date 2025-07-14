"""Conan Provider Plugin

This module implements the Conan provider plugin for CPPython. It handles
integration with the Conan package manager, including dependency resolution,
installation, and synchronization with other tools.
"""

import logging
from pathlib import Path
from typing import Any

import requests
from conan.api.conan_api import ConanAPI
from conan.api.model import ListPattern
from conan.internal.model.profile import Profile

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
        """Install/update dependencies using Conan API.

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

            # Initialize Conan API
            conan_api = ConanAPI()

            # Get project paths
            project_root = self.core_data.project_data.project_root
            conanfile_path = project_root / 'conanfile.py'

            if not conanfile_path.exists():
                raise ProviderInstallationError('conan', 'Generated conanfile.py not found')

            # Get all remotes
            all_remotes = conan_api.remotes.list()
            logger.debug('Available remotes: %s', [remote.name for remote in all_remotes])

            # Get profiles with fallback to auto-detection
            profile_host, profile_build = self._get_profiles(conan_api)

            path = str(conanfile_path)
            remotes = all_remotes
            update_flag = None if not update else True
            check_updates_flag = update

            deps_graph = conan_api.graph.load_graph_consumer(
                path=path,
                name=None,
                version=None,
                user=None,
                channel=None,
                lockfile=None,
                remotes=remotes,
                update=update_flag,
                check_updates=check_updates_flag,
                is_build_require=False,
                profile_host=profile_host,
                profile_build=profile_build,
            )

            logger.debug('Dependency graph loaded with %d nodes', len(deps_graph.nodes))

            # Analyze binaries to determine what needs to be built/downloaded
            conan_api.graph.analyze_binaries(
                graph=deps_graph,
                build_mode=['missing'],  # Only build what's missing
                remotes=all_remotes,
                update=None if not update else True,
                lockfile=None,
            )

            # Install all dependencies
            conan_api.install.install_binaries(deps_graph=deps_graph, remotes=all_remotes)

            # Generate files for the consumer (conandata.yml, conan_toolchain.cmake, etc.)
            conan_api.install.install_consumer(
                deps_graph=deps_graph,
                generators=['CMakeToolchain', 'CMakeDeps'],
                source_folder=str(project_root),
                output_folder=str(self.core_data.cppython_data.build_path),
            )

            logger.debug('Successfully installed dependencies using Conan API')

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

        # Step 2: Get profiles with fallback to auto-detection
        profile_host, profile_build = self._get_profiles(conan_api)

        # Step 3: Build dependency graph for the package - prepare parameters
        path = str(conanfile_path)
        remotes = all_remotes  # Use all remotes for dependency resolution

        deps_graph = conan_api.graph.load_graph_consumer(
            path=path,
            name=None,
            version=None,
            user=None,
            channel=None,
            lockfile=None,
            remotes=remotes,
            update=None,
            check_updates=False,
            is_build_require=False,
            profile_host=profile_host,
            profile_build=profile_build,
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

    def _apply_profile_processing(self, profiles: list[Profile], conan_api: ConanAPI, cache_settings: Any) -> None:
        """Apply profile plugin and settings processing to a list of profiles.

        Args:
            profiles: List of profiles to process
            conan_api: The Conan API instance
            cache_settings: The settings configuration
        """
        logger = logging.getLogger('cppython.conan')

        # Apply profile plugin processing
        try:
            profile_plugin = conan_api.profiles._load_profile_plugin()
            if profile_plugin is not None:
                for profile in profiles:
                    try:
                        profile_plugin(profile)
                    except Exception as plugin_error:
                        logger.warning('Profile plugin failed for profile: %s', str(plugin_error))
        except (AttributeError, Exception):
            logger.debug('Profile plugin not available or failed to load')

        # Process settings to initialize processed_settings
        for profile in profiles:
            try:
                profile.process_settings(cache_settings)
            except (AttributeError, Exception) as settings_error:
                logger.debug('Settings processing failed for profile: %s', str(settings_error))

    def _get_profiles(self, conan_api: ConanAPI) -> tuple[Profile, Profile]:
        """Get Conan profiles with fallback to auto-detection.

        Args:
            conan_api: The Conan API instance

        Returns:
            A tuple of (profile_host, profile_build) objects
        """
        logger = logging.getLogger('cppython.conan')

        try:
            # Gather default profile paths, these can raise exceptions if not available
            profile_host_path = conan_api.profiles.get_default_host()
            profile_build_path = conan_api.profiles.get_default_build()

            # Load the actual profile objects, can raise if data is invalid
            profile_host = conan_api.profiles.get_profile([profile_host_path])
            profile_build = conan_api.profiles.get_profile([profile_build_path])

            logger.debug('Using existing default profiles')
            return profile_host, profile_build

        except Exception as e:
            logger.warning('Default profiles not available, using auto-detection. Conan message: %s', str(e))

            # Create auto-detected profiles
            profiles = [conan_api.profiles.detect(), conan_api.profiles.detect()]
            cache_settings = conan_api.config.settings_yml

            # Apply profile plugin processing to both profiles
            self._apply_profile_processing(profiles, conan_api, cache_settings)

            logger.debug('Auto-detected profiles with plugin processing applied')
            return profiles[0], profiles[1]
