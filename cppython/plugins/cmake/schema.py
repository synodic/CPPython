"""CMake plugin schema

This module defines the schema and data models for integrating the CMake
generator with CPPython. It includes definitions for cache variables,
configuration presets, and synchronization data.
"""

from enum import StrEnum
from pathlib import Path
from typing import Annotated

from pydantic import Field

from cppython.core.schema import CPPythonModel, SyncData


class VariableType(StrEnum):
    """Defines the types of variables that can be used in CMake cache.

    Args:
        Enum: Base class for creating enumerations.
    """

    BOOL = 'BOOL'
    PATH = 'PATH'
    FILEPATH = 'FILEPATH'
    STRING = 'STRING'
    INTERNAL = 'INTERNAL'
    STATIC = 'STATIC'
    UNINITIALIZED = 'UNINITIALIZED'


class CacheVariable(CPPythonModel, extra='forbid'):
    """Represents a variable in the CMake cache.

    Attributes:
        type: The type of the variable (e.g., BOOL, PATH).
        value: The value of the variable, which can be a boolean or string.
    """

    type: None | VariableType = None
    value: bool | str


class ConfigurePreset(CPPythonModel, extra='allow'):
    """Partial Configure Preset specification to allow cache variable injection"""

    name: str
    description: Annotated[str | None, Field(description='A human-readable description of the preset.')] = None

    hidden: Annotated[bool | None, Field(description='If true, the preset is hidden and cannot be used directly.')] = (
        None
    )

    inherits: Annotated[
        str | list[str] | None, Field(description='The inherits field allows inheriting from other presets.')
    ] = None
    binaryDir: Annotated[
        str | None,
        Field(description='The path to the output binary directory.'),
    ] = None
    toolchainFile: Annotated[
        str | Path | None,
        Field(description='Path to the toolchain file.'),
    ] = None
    cacheVariables: dict[str, None | bool | str | CacheVariable] | None = None


class BuildPreset(CPPythonModel, extra='allow'):
    """Partial Build Preset specification for CMake build presets"""

    name: str
    description: Annotated[str | None, Field(description='A human-readable description of the preset.')] = None

    hidden: Annotated[bool | None, Field(description='If true, the preset is hidden and cannot be used directly.')] = (
        None
    )

    inherits: Annotated[
        str | list[str] | None, Field(description='The inherits field allows inheriting from other presets.')
    ] = None
    configurePreset: Annotated[
        str | None,
        Field(description='The name of a configure preset to associate with this build preset.'),
    ] = None
    configuration: Annotated[
        str | None,
        Field(description='Build configuration. Equivalent to --config on the command line.'),
    ] = None


class CMakePresets(CPPythonModel, extra='allow'):
    """The schema for the CMakePresets and CMakeUserPresets files."""

    version: Annotated[int, Field(description='The version of the JSON schema.')] = 9
    include: Annotated[
        list[str] | None, Field(description='The include field allows inheriting from another preset.')
    ] = None
    configurePresets: Annotated[list[ConfigurePreset] | None, Field(description='The list of configure presets')] = None
    buildPresets: Annotated[list[BuildPreset] | None, Field(description='The list of build presets')] = None


class CMakeSyncData(SyncData):
    """The CMake sync data"""

    toolchain_file: Path | None = None


class CMakeData(CPPythonModel):
    """Resolved CMake data"""

    preset_file: Path
    configuration_name: str


class CMakeConfiguration(CPPythonModel):
    """Configuration"""

    preset_file: Annotated[
        Path,
        Field(
            description='The CMakePreset.json file that will be managed by CPPython. Will'
            " be searched for the given 'configuration_name'",
        ),
    ] = Path('CMakePresets.json')
    configuration_name: Annotated[
        str,
        Field(
            description='The CMake configuration preset to look for and override inside the given `preset_file`. '
            'Additional configurations will be added using this option as the base. For example, given "default", '
            '"default-release" will also be written'
        ),
    ] = 'default'
