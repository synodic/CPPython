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
            logger.debug('Conan API initialized successfully')

            # Get project paths
            project_root = self.core_data.project_data.project_root
            conanfile_path = project_root / 'conanfile.py'
            logger.debug('Project root: %s, Conanfile path: %s', project_root, conanfile_path)

            if not conanfile_path.exists():
                raise ProviderInstallationError('conan', 'Generated conanfile.py not found')

            # Get all remotes
            try:
                all_remotes = conan_api.remotes.list()
                logger.debug('Available remotes: %s', [remote.name for remote in all_remotes])
            except Exception as e:
                logger.error('Failed to list remotes: %s', e)
                raise

            # Get profiles from resolved data
            profile_host, profile_build = self.data.host_profile, self.data.build_profile
            logger.debug('Using profiles - host: %s, build: %s', profile_host, profile_build)

            path = str(conanfile_path)
            remotes = all_remotes
            update_flag = None if not update else True
            check_updates_flag = update

            logger.debug('Loading dependency graph with parameters: path=%s, remotes=%d, update=%s, check_updates=%s', 
                        path, len(remotes), update_flag, check_updates_flag)

            try:
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
                logger.debug('Dependency graph loaded successfully, type: %s', type(deps_graph))
                if hasattr(deps_graph, 'nodes'):
                    logger.debug('Graph has %d nodes', len(deps_graph.nodes))
                else:
                    logger.warning('Dependency graph does not have nodes attribute')
            except Exception as e:
                logger.error('Failed to load dependency graph: %s', e)
                raise

            # Analyze binaries to determine what needs to be built/downloaded
            logger.debug('Starting binary analysis with build_mode=["missing"], update=%s', update)
            try:
                conan_api.graph.analyze_binaries(
                    graph=deps_graph,
                    build_mode=['missing'],  # Only build what's missing
                    remotes=all_remotes,
                    update=None if not update else True,
                    lockfile=None,
                )
                logger.debug('Binary analysis completed successfully')
            except Exception as e:
                logger.error('Failed to analyze binaries: %s', e)
                raise

            # Install all dependencies
            logger.debug('Starting binary installation')
            try:
                conan_api.install.install_binaries(deps_graph=deps_graph, remotes=all_remotes)
                logger.debug('Binary installation completed successfully')
            except Exception as e:
                logger.error('Failed to install binaries: %s', e)
                raise

            # Generate files for the consumer (conandata.yml, conan_toolchain.cmake, etc.)
            logger.debug('Generating consumer files with generators=["CMakeToolchain", "CMakeDeps"]')
            logger.debug('Source folder: %s, Output folder: %s', project_root, self.core_data.cppython_data.build_path)
            try:
                conan_api.install.install_consumer(
                    deps_graph=deps_graph,
                    generators=['CMakeToolchain', 'CMakeDeps'],
                    source_folder=str(project_root),
                    output_folder=str(self.core_data.cppython_data.build_path),
                )
                logger.debug('Consumer file generation completed successfully')
            except Exception as e:
                logger.error('Failed to install consumer files: %s', e)
                raise

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
        logger = logging.getLogger('cppython.conan')
        logger.debug('Starting package publish workflow')
        
        # Get the project root directory where conanfile.py should be located
        project_root = self.core_data.project_data.project_root
        conanfile_path = project_root / 'conanfile.py'
        logger.debug('Project root: %s, Conanfile path: %s', project_root, conanfile_path)

        if not conanfile_path.exists():
            raise FileNotFoundError(f'conanfile.py not found at {conanfile_path}')

        # Initialize Conan API
        try:
            conan_api = ConanAPI()
            logger.debug('Conan API initialized successfully for publish')
        except Exception as e:
            logger.error('Failed to initialize Conan API for publish: %s', e)
            raise

        # Get configured remotes from Conan API and filter by our configuration
        # TODO: We want to replace the global conan remotes with the ones configured in CPPython.
        try:
            all_remotes = conan_api.remotes.list()
            logger.debug('Retrieved %d remotes for publish', len(all_remotes))
        except Exception as e:
            logger.error('Failed to list remotes for publish: %s', e)
            raise
            
        if not self.data.local_only:
            # Filter remotes to only include those specified in configuration
            configured_remotes = [remote for remote in all_remotes if remote.name in self.data.remotes]
            logger.debug('Configured remotes: %s', [r.name for r in configured_remotes])

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
            logger.debug('Local only mode - no remotes configured')

        # Step 1: Export the recipe to the cache
        # This is equivalent to the export part of `conan create`
        logger.debug('Starting export step with path: %s', conanfile_path)
        try:
            ref, conanfile = conan_api.export.export(
                path=str(conanfile_path),
                name=None,
                version=None,
                user=None,
                channel=None,
                lockfile=None,
                remotes=all_remotes,  # Use all remotes for dependency resolution during export
            )
            logger.debug('Export completed successfully. Ref: %s, Conanfile type: %s', ref, type(conanfile))
            if conanfile is None:
                logger.error('Export returned None for conanfile!')
            else:
                conanfile_attrs = dir(conanfile) if hasattr(conanfile, '__dict__') else 'No attributes'
                logger.debug('Conanfile attributes: %s', conanfile_attrs)
        except Exception as e:
            logger.error('Export failed: %s', e)
            raise

        # Step 2: Get profiles from resolved data
        profile_host, profile_build = self.data.host_profile, self.data.build_profile
        logger.debug('Using profiles for publish - host: %s, build: %s', profile_host, profile_build)

        # Step 3: Build dependency graph for the package - prepare parameters
        path = str(conanfile_path)
        remotes = all_remotes  # Use all remotes for dependency resolution
        logger.debug('Loading dependency graph for publish with path: %s', path)

        try:
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
            logger.debug('Dependency graph loaded successfully for publish')
        except Exception as e:
            logger.error('Failed to load dependency graph for publish: %s', e)
            raise

        # Step 4: Analyze binaries and install/build them if needed
        logger.debug('Starting binary analysis for publish')
        try:
            conan_api.graph.analyze_binaries(
                graph=deps_graph,
                build_mode=['*'],  # Build from source (equivalent to the create behavior)
                remotes=all_remotes,  # Use all remotes for dependency resolution
                update=None,
                lockfile=None,
            )
            logger.debug('Binary analysis completed for publish')
        except Exception as e:
            logger.error('Failed to analyze binaries for publish: %s', e)
            raise

        # Step 5: Install all dependencies and build the package
        logger.debug('Starting binary installation for publish')
        try:
            conan_api.install.install_binaries(deps_graph=deps_graph, remotes=all_remotes)
            logger.debug('Binary installation completed for publish')
        except Exception as e:
            logger.error('Failed to install binaries for publish: %s', e)
            raise

        # If not local only, upload the package
        if not self.data.local_only:
            logger.debug('Starting package upload (not local only)')
            # Get all packages matching the created reference
            try:
                logger.debug('Creating ref pattern with ref.name: %s (ref type: %s)', ref.name, type(ref))
                ref_pattern = ListPattern(f'{ref.name}/*', package_id='*', only_recipe=False)
                package_list = conan_api.list.select(ref_pattern)
                recipe_count = len(package_list.recipes) if package_list.recipes else 0
                logger.debug('Package list retrieved: %s recipes found', recipe_count)
            except AttributeError as e:
                logger.error('Failed to access ref.name - ref object: %s, error: %s', ref, e)
                raise
            except Exception as e:
                logger.error('Failed to get package list for upload: %s', e)
                raise

            if package_list.recipes:
                # Use the first configured remote for upload
                remote = configured_remotes[0]
                logger.debug('Uploading to remote: %s', remote.name)

                try:
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
                    logger.debug('Package upload completed successfully')
                except Exception as e:
                    logger.error('Failed to upload package: %s', e)
                    raise
            else:
                raise ProviderInstallationError('conan', 'No packages found to upload')
        else:
            logger.debug('Local only mode - skipping upload')
