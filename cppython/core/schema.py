"""Data types for CPPython that encapsulate the requirements between the plugins and the core library"""

from abc import abstractmethod
from pathlib import Path
from typing import Any, NewType, Protocol

from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic.types import DirectoryPath, FilePath

from cppython.utility.plugin import Plugin as SynodicPlugin
from cppython.utility.utility import TypeName


class CPPythonModel(BaseModel):
    """The base model to use for all CPPython models"""

    model_config = {"populate_by_name": False}


class ProjectData(CPPythonModel, extra="forbid"):
    """Resolved data of 'ProjectConfiguration'"""

    pyproject_file: FilePath = Field(description="The path where the pyproject.toml exists")
    verbosity: int = Field(default=0, description="The verbosity level as an integer [0,2]")


class ProjectConfiguration(CPPythonModel, extra="forbid"):
    """Project-wide configuration"""

    pyproject_file: FilePath = Field(description="The path where the pyproject.toml exists")
    version: str | None = Field(
        description=(
            "The version number a 'dynamic' project version will resolve to. If not provided a CPPython project will"
            " initialize its SCM plugins to discover any available version"
        )
    )
    verbosity: int = Field(default=0, description="The verbosity level as an integer [0,2]")
    debug: bool = Field(
        default=False, description="Debug mode. Additional processing will happen to expose more debug information"
    )

    @field_validator("verbosity")
    @classmethod
    def min_max(cls, value: int) -> int:
        """Validator that clamps the input value

        Args:
            value: Input to validate

        Returns:
            The clamped input value
        """
        return min(max(value, 0), 2)

    @field_validator("pyproject_file")
    @classmethod
    def pyproject_name(cls, value: FilePath) -> FilePath:
        """Validator that verifies the name of the file

        Args:
            value: Input to validate

        Raises:
            ValueError: The given filepath is not named "pyproject.toml"

        Returns:
            The file path
        """

        if value.name != "pyproject.toml":
            raise ValueError('The given file is not named "pyproject.toml"')

        return value


class PEP621Data(CPPythonModel):
    """Resolved PEP621Configuration data"""

    name: str
    version: str
    description: str


class PEP621Configuration(CPPythonModel):
    """CPPython relevant PEP 621 conforming data
    Because only the partial schema is used, we ignore 'extra' attributes
        Schema: https://www.python.org/dev/peps/pep-0621/
    """

    dynamic: list[str] = Field(default=[], description="https://peps.python.org/pep-0621/#dynamic")
    name: str = Field(description="https://peps.python.org/pep-0621/#name")
    version: str | None = Field(default=None, description="https://peps.python.org/pep-0621/#version")
    description: str = Field(default="", description="https://peps.python.org/pep-0621/#description")

    @model_validator(mode="after")  # type: ignore
    @classmethod
    def dynamic_data(cls, model: "PEP621Configuration") -> "PEP621Configuration":
        """Validates that dynamic data is represented correctly

        Args:
            model: The input model data

        Raises:
            ValueError: If dynamic versioning is incorrect

        Returns:
            The data
        """

        for field in model.model_fields.keys():
            if field == "dynamic":
                continue
            value = getattr(model, field)
            if field not in model.dynamic:
                if value is None:
                    raise ValueError(f"'{field}' is not a dynamic field. It must be defined")
            else:
                if value is not None:
                    raise ValueError(f"'{field}' is a dynamic field. It must not be defined")

        return model


def _default_install_location() -> Path:
    return Path.home() / ".cppython"


class CPPythonData(CPPythonModel, extra="forbid"):
    """Resolved CPPython data with local and global configuration"""

    install_path: DirectoryPath
    tool_path: DirectoryPath
    build_path: DirectoryPath
    current_check: bool
    provider_name: TypeName
    generator_name: TypeName
    scm_name: TypeName

    @field_validator("install_path", "tool_path", "build_path")
    @classmethod
    def validate_absolute_path(cls, value: DirectoryPath) -> DirectoryPath:
        """Enforce the input is an absolute path

        Args:
            value: The input value

        Raises:
            ValueError: Raised if the input is not an absolute path

        Returns:
            The validated input value
        """
        if not value.is_absolute():
            raise ValueError("Absolute path required")

        return value


CPPythonPluginData = NewType("CPPythonPluginData", CPPythonData)


class SyncData(CPPythonModel):
    """Data that passes in a plugin sync"""

    provider_name: TypeName


class SupportedFeatures(CPPythonModel):
    """Plugin feature support"""

    initialization: bool = Field(
        default=False, description="Whether the plugin supports initialization from an empty state"
    )


class Information(CPPythonModel):
    """Plugin information that complements the packaged project metadata"""


class PluginGroupData(CPPythonModel, extra="forbid"):
    """Plugin group data"""

    root_directory: DirectoryPath = Field(description="The directory of the project")
    tool_directory: DirectoryPath = Field(
        description=(
            "Points to the project plugin directory within the tool directory. This directory is for project specific"
            " cached data."
        )
    )


class Plugin(SynodicPlugin, Protocol):
    """CPPython plugin"""

    @abstractmethod
    def __init__(self, group_data: PluginGroupData) -> None:
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def features(directory: DirectoryPath) -> SupportedFeatures:
        """Broadcasts the shared features of the plugin to CPPython

        Args:
            directory: The root directory where features are evaluated

        Returns:
            The supported features
        """
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def information() -> Information:
        """Retrieves plugin information that complements the packaged project metadata

        Returns:
            The plugin's information
        """
        raise NotImplementedError


class DataPluginGroupData(PluginGroupData):
    """Data plugin group data"""


class CorePluginData(CPPythonModel):
    """Core resolved data that will be passed to data plugins"""

    project_data: ProjectData
    pep621_data: PEP621Data
    cppython_data: CPPythonPluginData


class SupportedDataFeatures(SupportedFeatures):
    """Data plugin feature support"""


class DataPlugin(Plugin, Protocol):
    """Abstract plugin type for internal CPPython data"""

    @abstractmethod
    def __init__(
        self, group_data: DataPluginGroupData, core_data: CorePluginData, configuration_data: dict[str, Any]
    ) -> None:
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def features(directory: DirectoryPath) -> SupportedDataFeatures:
        """Broadcasts the shared features of the data plugin to CPPython

        Args:
            directory: The root directory where features are evaluated

        Returns:
            The supported features
        """
        raise NotImplementedError

    @classmethod
    async def download_tooling(cls, directory: DirectoryPath) -> None:
        """Installs the external tooling required by the plugin. Should be overridden if required

        Args:
            directory: The directory to download any extra tooling to
        """


class CPPythonGlobalConfiguration(CPPythonModel, extra="forbid"):
    """Global data extracted by the tool"""

    current_check: bool = Field(default=True, alias="current-check", description="Checks for a new CPPython version")


ProviderData = NewType("ProviderData", dict[str, Any])
GeneratorData = NewType("GeneratorData", dict[str, Any])


class CPPythonLocalConfiguration(CPPythonModel, extra="forbid"):
    """Data required by the tool"""

    install_path: Path = Field(
        default=_default_install_location(), alias="install-path", description="The global install path for the project"
    )
    tool_path: Path = Field(
        default=Path("tool"), alias="tool-path", description="The local tooling path for the project"
    )
    build_path: Path = Field(
        default=Path("build"), alias="build-path", description="The local build path for the project"
    )
    provider: ProviderData = Field(
        default=ProviderData({}), description="Provider plugin data associated with 'provider_name"
    )
    provider_name: TypeName | None = Field(
        default=None, alias="provider-name", description="If empty, the provider will be automatically deduced."
    )
    generator: GeneratorData = Field(
        default=GeneratorData({}), description="Generator plugin data associated with 'generator_name'"
    )
    generator_name: TypeName | None = Field(
        default=None, alias="generator-name", description="If empty, the generator will be automatically deduced."
    )


class ToolData(CPPythonModel):
    """Tool entry of pyproject.toml"""

    cppython: CPPythonLocalConfiguration | None = Field(description="CPPython tool data", default=None)


class PyProject(CPPythonModel):
    """pyproject.toml schema"""

    project: PEP621Configuration = Field(description="PEP621: https://www.python.org/dev/peps/pep-0621/")
    tool: ToolData | None = Field(description="Tool data", default=None)


class CoreData(CPPythonModel):
    """Core resolved data that will be resolved"""

    project_data: ProjectData
    cppython_data: CPPythonData


class Interface(Protocol):
    """Type for interfaces to allow feedback from CPPython"""

    @abstractmethod
    def write_pyproject(self) -> None:
        """Called when CPPython requires the interface to write out pyproject.toml changes"""
        raise NotImplementedError

    @abstractmethod
    def write_configuration(self) -> None:
        """Called when CPPython requires the interface to write out configuration changes"""
        raise NotImplementedError
