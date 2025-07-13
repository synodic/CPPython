"""Provides functionality to resolve Conan-specific data for the CPPython project."""

from typing import Any

from packaging.requirements import Requirement

from cppython.core.exception import ConfigException
from cppython.core.schema import CorePluginData
from cppython.plugins.conan.schema import ConanConfiguration, ConanData, ConanDependency


def resolve_conan_dependency(requirement: Requirement) -> ConanDependency:
    """Resolves a Conan dependency from a requirement"""
    specifiers = requirement.specifier

    # If the length of specifiers is greater than one, raise a configuration error
    if len(specifiers) > 1:
        raise ConfigException('Multiple specifiers are not supported. Please provide a single specifier.', [])

    # Extract the version from the single specifier
    min_version = None
    if len(specifiers) == 1:
        specifier = next(iter(specifiers))
        if specifier.operator != '>=':
            raise ConfigException(f"Unsupported specifier '{specifier.operator}'. Only '>=' is supported.", [])
        min_version = specifier.version

    return ConanDependency(
        name=requirement.name,
        version_ge=min_version,
    )


def resolve_conan_data(data: dict[str, Any], core_data: CorePluginData) -> ConanData:
    """Resolves the conan data

    Args:
        data: The data to resolve
        core_data: The core plugin data

    Returns:
        The resolved conan data
    """
    parsed_data = ConanConfiguration(**data)

    return ConanData(remotes=parsed_data.remotes)
