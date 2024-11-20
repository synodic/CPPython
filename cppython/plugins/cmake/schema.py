"""CMake data definitions"""

from enum import Enum, auto
from pathlib import Path
from typing import Annotated

from pydantic import Field
from pydantic.types import FilePath

from cppython.core.schema import CPPythonModel, SyncData


class VariableType(Enum):
    """_summary_

    Args:
        Enum: _description_
    """

    BOOL = (auto(),)  # Boolean ON/OFF value.
    PATH = (auto(),)  # Path to a directory.
    FILEPATH = (auto(),)  # Path to a file.
    STRING = (auto(),)  # Generic string value.
    INTERNAL = (auto(),)  # Do not present in GUI at all.
    STATIC = (auto(),)  # Value managed by CMake, do not change.
    UNINITIALIZED = auto()  # Type not yet specified.


class CacheVariable(CPPythonModel, extra='forbid'):
    """_summary_"""

    type: None | VariableType
    value: bool | str


class ConfigurePreset(CPPythonModel, extra='allow'):
    """Partial Configure Preset specification to allow cache variable injection"""

    name: str
    cacheVariables: dict[str, None | bool | str | CacheVariable] | None


class CMakePresets(CPPythonModel, extra='allow'):
    """The schema for the CMakePresets and CMakeUserPresets files.

    The only information needed is the configure preset list for cache variable injection
    """

    configurePresets: Annotated[list[ConfigurePreset], Field(description='The list of configure presets')] = []


class CMakeSyncData(SyncData):
    """The CMake sync data"""

    top_level_includes: FilePath


class CMakeData(CPPythonModel):
    """Resolved CMake data"""

    preset_file: FilePath
    configuration_name: str


class CMakeConfiguration(CPPythonModel):
    """Configuration"""

    preset_file: Annotated[
        FilePath,
        Field(
            description="The CMakePreset.json file that will be searched for the given 'configuration_name'",
        ),
    ] = Path('CMakePresets.json')
    configuration_name: Annotated[str, Field(description='The CMake configuration preset to look for and override')]
