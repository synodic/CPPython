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
        """Common implementation for installing/updating dependencies.

        Args:
            update: If True, check remotes for newer versions/revisions and install those.
                   If False, use cached versions when available.
        """
        try:
            resolved_dependencies = [resolve_conan_dependency(req) for req in self.core_data.cppython_data.dependencies]

            self.builder.generate_conanfile(self.core_data.project_data.project_root, resolved_dependencies)

            self.core_data.cppython_data.build_path.mkdir(parents=True, exist_ok=True)

            # Install/update dependencies using Conan API
            project_root = self.core_data.project_data.project_root
            conanfile_path = project_root / 'conanfile.py'

            if conanfile_path.exists():
                # Initialize Conan API
                conan_api = ConanAPI()

                # Get default profiles
                profile_host_path = conan_api.profiles.get_default_host()
                profile_build_path = conan_api.profiles.get_default_build()
                profile_host = conan_api.profiles.get_profile([profile_host_path])
                profile_build = conan_api.profiles.get_profile([profile_build_path])

                # Build dependency graph for the package
                deps_graph = conan_api.graph.load_graph_consumer(
                    path=str(conanfile_path),
                    name=None,
                    version=None,
                    user=None,
                    channel=None,
                    profile_host=profile_host,
                    profile_build=profile_build,
                    lockfile=None,
                    remotes=conan_api.remotes.list(),
                    update=update,
                    check_updates=update,
                    is_build_require=False,
                )

                # Install dependencies
                conan_api.install.install_binaries(deps_graph=deps_graph, remotes=conan_api.remotes.list())
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

        # Step 1: Export the recipe to the cache
        # This is equivalent to the export part of `conan create`
        ref, conanfile = conan_api.export.export(
            path=str(conanfile_path),
            name=None,
            version=None,
            user=None,
            channel=None,
            lockfile=None,
            remotes=conan_api.remotes.list(),
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
            remotes=conan_api.remotes.list(),
            update=None,
            check_updates=False,
            is_build_require=False,
        )

        # Step 4: Analyze binaries and install/build them if needed
        conan_api.graph.analyze_binaries(
            graph=deps_graph,
            build_mode=['*'],  # Build from source (equivalent to the create behavior)
            remotes=conan_api.remotes.list(),
            update=None,
            lockfile=None,
        )

        # Step 5: Install all dependencies and build the package
        conan_api.install.install_binaries(deps_graph=deps_graph, remotes=conan_api.remotes.list())

        # If not local, upload the package
        if not self.data.local:
            # Get all packages matching the created reference
            ref_pattern = ListPattern(f'{ref.name}/*', package_id='*', only_recipe=False)
            package_list = conan_api.list.select(ref_pattern)

            if package_list.recipes:
                # Get the first configured remote or raise an error
                remotes = conan_api.remotes.list()
                if not remotes:
                    raise ProviderConfigurationError('conan', 'No remotes configured for upload', 'remotes')

                remote = remotes[0]  # Use first remote

                # Upload the package
                conan_api.upload.upload_full(
                    package_list=package_list,
                    remote=remote,
                    enabled_remotes=remotes,
                    check_integrity=False,
                    force=False,
                    metadata=None,
                    dry_run=False,
                )
            else:
                raise ProviderInstallationError('conan', 'No packages found to upload')
