"""Builder to help build vcpkg state"""

from typing import Any

from packaging.requirements import Requirement

from cppython.core.exception import ConfigException
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

    root_directory = core_data.project_data.project_root.absolute()

    modified_install_directory = parsed_data.install_directory

    # Add the project location to all relative paths
    if not modified_install_directory.is_absolute():
        modified_install_directory = root_directory / modified_install_directory

    # Create directories
    modified_install_directory.mkdir(parents=True, exist_ok=True)

    vcpkg_dependencies: list[VcpkgDependency] = []
    for requirement in core_data.cppython_data.dependencies:
        resolved_dependency = resolve_vcpkg_dependency(requirement)
        vcpkg_dependencies.append(resolved_dependency)

    return VcpkgData(
        install_directory=modified_install_directory,
        dependencies=vcpkg_dependencies,
    )


def resolve_vcpkg_dependency(requirement: Requirement) -> VcpkgDependency:
    """Resolve a VcpkgDependency from a packaging requirement.

    Args:
        requirement: A packaging requirement object.

    Returns:
        A resolved VcpkgDependency object.
    """
    specifiers = requirement.specifier

    # If the length of specifiers is greater than one, raise a configuration error
    if len(specifiers) > 1:
        raise ConfigException('Multiple specifiers are not supported. Please provide a single specifier.', [])

    # Extract the version from the single specifier
    version = None
    if len(specifiers) == 1:
        specifier = next(iter(specifiers))
        if specifier.operator != '>=':
            raise ConfigException(f"Unsupported specifier '{specifier.operator}'. Only '>=' is supported.", [])
        version = specifier.version

    return VcpkgDependency(
        name=requirement.name,
        default_features=True,
        features=[],
        version=version,
        platform=None,
        host=False,
    )
