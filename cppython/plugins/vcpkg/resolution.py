"""Builder to help build vcpkg state"""

from typing import Any

from cppython.core.schema import CorePluginData
from cppython.plugins.vcpkg.schema import (
    Manifest,
    VcpkgConfiguration,
    VcpkgData,
    VcpkgDependency,
)


def generate_manifest(core_data: CorePluginData, data: VcpkgData) -> Manifest:
    """From the input configuration data, construct a Vcpkg specific Manifest type

    Args:
        core_data: The core data to help with the resolve
        data: Converted vcpkg data

    Returns:
        The manifest
    """
    manifest = {
        'name': core_data.pep621_data.name,
        'version_string': core_data.pep621_data.version,
        'dependencies': data.dependencies,
    }

    return Manifest(**manifest)


def resolve_vcpkg_data(data: dict[str, Any], core_data: CorePluginData) -> VcpkgData:
    """Resolves the input data table from defaults to requirements

    Args:
        data: The input table
        core_data: The core data to help with the resolve

    Returns:
        The resolved data
    """
    parsed_data = VcpkgConfiguration(**data)

    root_directory = core_data.project_data.pyproject_file.parent.absolute()

    modified_install_directory = parsed_data.install_directory

    # Add the project location to all relative paths
    if not modified_install_directory.is_absolute():
        modified_install_directory = root_directory / modified_install_directory

    # Create directories
    modified_install_directory.mkdir(parents=True, exist_ok=True)

    vcpkg_dependencies: list[VcpkgDependency] = []
    for dependency in parsed_data.dependencies:
        vcpkg_dependency = VcpkgDependency(name=dependency.name)
        vcpkg_dependencies.append(vcpkg_dependency)

    return VcpkgData(
        install_directory=modified_install_directory,
        dependencies=vcpkg_dependencies,
    )
