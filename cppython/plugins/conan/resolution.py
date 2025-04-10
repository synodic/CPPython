"""Provides functionality to resolve Conan-specific data for the CPPython project."""

from typing import Any

from cppython.core.schema import CorePluginData
from cppython.plugins.conan.schema import ConanData


def resolve_conan_data(data: dict[str, Any], core_data: CorePluginData) -> ConanData:
    """Resolves the conan data

    Args:
        data: The data to resolve
        core_data: The core plugin data

    Returns:
        The resolved conan data
    """
    # parsed_data = ConanConfiguration(**data)
    # root_directory = core_data.project_data.pyproject_file.parent.absolute()

    return ConanData()
