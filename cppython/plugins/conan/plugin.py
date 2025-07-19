"""Conan Provider Plugin

This module implements the Conan provider plugin for CPPython. It handles
integration with the Conan package manager, including dependency resolution,
installation, and synchronization with other tools.
"""

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
        operation = 'update' if update else 'install'

        try:
            # Setup environment and generate conanfile
            conan_api, conanfile_path = self._prepare_installation()
        except Exception as e:
            raise ProviderInstallationError('conan', f'Failed to prepare {operation} environment: {e}', e) from e

        try:
            # Load dependency graph
            deps_graph = self._load_dependency_graph(conan_api, conanfile_path, update)
        except Exception as e:
            raise ProviderInstallationError('conan', f'Failed to load dependency graph: {e}', e) from e

        try:
            # Install dependencies
            self._install_binaries(conan_api, deps_graph, update)
        except Exception as e:
            raise ProviderInstallationError('conan', f'Failed to install binary dependencies: {e}', e) from e

        try:
            # Generate consumer files
            self._generate_consumer_files(conan_api, deps_graph)
        except Exception as e:
            raise ProviderInstallationError('conan', f'Failed to generate consumer files: {e}', e) from e

    def _prepare_installation(self) -> tuple[ConanAPI, Path]:
        """Prepare the installation environment and generate conanfile.

        Returns:
            Tuple of (ConanAPI instance, conanfile path)
        """
        # Resolve dependencies and generate conanfile.py
        resolved_dependencies = [resolve_conan_dependency(req) for req in self.core_data.cppython_data.dependencies]
        self.builder.generate_conanfile(self.core_data.project_data.project_root, resolved_dependencies)

        # Ensure build directory exists
        self.core_data.cppython_data.build_path.mkdir(parents=True, exist_ok=True)

        # Setup paths and API
        conan_api = ConanAPI()
        project_root = self.core_data.project_data.project_root
        conanfile_path = project_root / 'conanfile.py'

        if not conanfile_path.exists():
            raise FileNotFoundError('Generated conanfile.py not found')

        return conan_api, conanfile_path

    def _load_dependency_graph(self, conan_api: ConanAPI, conanfile_path: Path, update: bool):
        """Load and build the dependency graph.

        Args:
            conan_api: The Conan API instance
            conanfile_path: Path to the conanfile.py
            update: Whether to check for updates

        Returns:
            The loaded dependency graph
        """
        all_remotes = conan_api.remotes.list()
        profile_host, profile_build = self.data.host_profile, self.data.build_profile

        return conan_api.graph.load_graph_consumer(
            path=str(conanfile_path),
            name=None,
            version=None,
            user=None,
            channel=None,
            lockfile=None,
            remotes=all_remotes,
            update=update or None,
            check_updates=update,
            is_build_require=False,
            profile_host=profile_host,
            profile_build=profile_build,
        )

    def _install_binaries(self, conan_api: ConanAPI, deps_graph, update: bool) -> None:
        """Analyze and install binary dependencies.

        Args:
            conan_api: The Conan API instance
            deps_graph: The dependency graph
            update: Whether to check for updates
        """
        all_remotes = conan_api.remotes.list()

        # Analyze binaries to determine what needs to be built/downloaded
        conan_api.graph.analyze_binaries(
            graph=deps_graph,
            build_mode=['missing'],
            remotes=all_remotes,
            update=update or None,
            lockfile=None,
        )

        # Install all dependencies
        conan_api.install.install_binaries(deps_graph=deps_graph, remotes=all_remotes)

    def _generate_consumer_files(self, conan_api: ConanAPI, deps_graph) -> None:
        """Generate consumer files (CMake toolchain, deps, etc.).

        Args:
            conan_api: The Conan API instance
            deps_graph: The dependency graph
        """
        project_root = self.core_data.project_data.project_root

        conan_api.install.install_consumer(
            deps_graph=deps_graph,
            generators=['CMakeToolchain', 'CMakeDeps'],
            source_folder=str(project_root),
            output_folder=str(self.core_data.cppython_data.build_path),
        )

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

        raise NotSupportedError(f'Unsupported sync types: {consumer.sync_types()}')

    @classmethod
    async def download_tooling(cls, directory: Path) -> None:
        """Downloads the conan provider file"""
        cls._download_file(cls._provider_url, directory / 'conan_provider.cmake')

    def publish(self) -> None:
        """Publishes the package using conan create workflow."""
        project_root = self.core_data.project_data.project_root
        conanfile_path = project_root / 'conanfile.py'

        if not conanfile_path.exists():
            raise FileNotFoundError(f'conanfile.py not found at {conanfile_path}')

        conan_api = ConanAPI()
        all_remotes = conan_api.remotes.list()

        # Configure remotes for upload
        configured_remotes = self._get_configured_remotes(all_remotes)

        # Export the recipe to cache
        ref, _ = conan_api.export.export(
            path=str(conanfile_path),
            name=None,
            version=None,
            user=None,
            channel=None,
            lockfile=None,
            remotes=all_remotes,
        )

        # Build dependency graph and install
        profile_host, profile_build = self.data.host_profile, self.data.build_profile
        deps_graph = conan_api.graph.load_graph_consumer(
            path=str(conanfile_path),
            name=None,
            version=None,
            user=None,
            channel=None,
            lockfile=None,
            remotes=all_remotes,
            update=None,
            check_updates=False,
            is_build_require=False,
            profile_host=profile_host,
            profile_build=profile_build,
        )

        # Analyze and build binaries
        conan_api.graph.analyze_binaries(
            graph=deps_graph,
            build_mode=['*'],
            remotes=all_remotes,
            update=None,
            lockfile=None,
        )

        conan_api.install.install_binaries(deps_graph=deps_graph, remotes=all_remotes)

        # Upload if not local only
        if not self.data.local_only:
            self._upload_package(conan_api, ref, configured_remotes)

    def _get_configured_remotes(self, all_remotes):
        """Get and validate configured remotes for upload."""
        if self.data.local_only:
            return []

        configured_remotes = [remote for remote in all_remotes if remote.name in self.data.remotes]

        if not configured_remotes:
            available_remotes = [remote.name for remote in all_remotes]
            raise ProviderConfigurationError(
                'conan',
                f'No configured remotes found. Available: {available_remotes}, Configured: {self.data.remotes}',
                'remotes',
            )

        return configured_remotes

    def _upload_package(self, conan_api, ref, configured_remotes):
        """Upload the package to configured remotes."""
        ref_pattern = ListPattern(f'{ref.name}/*', package_id='*', only_recipe=False)
        package_list = conan_api.list.select(ref_pattern)

        if not package_list.recipes:
            raise ProviderInstallationError('conan', 'No packages found to upload')

        remote = configured_remotes[0]
        conan_api.upload.upload_full(
            package_list=package_list,
            remote=remote,
            enabled_remotes=configured_remotes,
            check_integrity=False,
            force=False,
            metadata=None,
            dry_run=False,
        )
