"""Data types for CPPython that encapsulate the requirements between the plugins and the core library"""

from abc import abstractmethod
from pathlib import Path
from typing import Annotated, Any, NewType, Protocol, runtime_checkable

from packaging.requirements import Requirement
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic.types import DirectoryPath

from cppython.utility.plugin import Plugin as SynodicPlugin
from cppython.utility.utility import TypeName


class CPPythonModel(BaseModel):
    """The base model to use for all CPPython models"""

    model_config = ConfigDict(validate_by_name=True, validate_by_alias=True, arbitrary_types_allowed=True)


class ProjectData(CPPythonModel, extra='forbid'):
    """Resolved data of 'ProjectConfiguration'"""

    project_root: Annotated[Path, Field(description='The path where the pyproject.toml exists')]
    verbosity: Annotated[int, Field(description='The verbosity level as an integer [0,2]')] = 0


class ProjectConfiguration(CPPythonModel, extra='forbid'):
    """Project-wide configuration"""

    project_root: Annotated[Path, Field(description='The path where the pyproject.toml exists')]
    version: Annotated[
        str | None,
        Field(
            description=(
                "The version number a 'dynamic' project version will resolve to. If not provided"
                'a CPPython project will'
                ' initialize its SCM plugins to discover any available version'
            )
        ),
    ]
    verbosity: Annotated[int, Field(description='The verbosity level as an integer [0,2]')] = 0
    debug: Annotated[
        bool, Field(description='Debug mode. Additional processing will happen to expose more debug information')
    ] = False

    @field_validator('verbosity')  # type: ignore
    @classmethod
    def min_max(cls, value: int) -> int:
        """Validator that clamps the input value

        Args:
            value: Input to validate

        Returns:
            The clamped input value
        """
        return min(max(value, 0), 2)


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

    dynamic: Annotated[list[str], Field(description='https://peps.python.org/pep-0621/#dynamic')] = []
    name: Annotated[str, Field(description='https://peps.python.org/pep-0621/#name')]
    version: Annotated[str | None, Field(description='https://peps.python.org/pep-0621/#version')] = None
    description: Annotated[str, Field(description='https://peps.python.org/pep-0621/#description')] = ''

    @model_validator(mode='after')  # type: ignore
    @classmethod
    def dynamic_data(cls, model: 'PEP621Configuration') -> 'PEP621Configuration':
        """Validates that dynamic data is represented correctly

        Args:
            model: The input model data

        Raises:
            ValueError: If dynamic versioning is incorrect

        Returns:
            The data
        """
        for field in PEP621Configuration.model_fields:
            if field == 'dynamic':
                continue
            value = getattr(model, field)
            if field not in model.dynamic:
                if value is None:
                    raise ValueError(f"'{field}' is not a dynamic field. It must be defined")
            elif value is not None:
                raise ValueError(f"'{field}' is a dynamic field. It must not be defined")

        return model


class CPPythonData(CPPythonModel, extra='forbid'):
    """Resolved CPPython data with local and global configuration"""

    configuration_path: Path
    install_path: Path
    tool_path: Path
    build_path: Path
    current_check: bool
    provider_name: TypeName
    generator_name: TypeName
    scm_name: TypeName
    dependencies: list[Requirement]

    @field_validator('configuration_path', 'install_path', 'tool_path', 'build_path')  # type: ignore
    @classmethod
    def validate_absolute_path(cls, value: Path) -> Path:
        """Enforce the input is an absolute path

        Args:
            value: The input value

        Raises:
            ValueError: Raised if the input is not an absolute path

        Returns:
            The validated input value
        """
        if not value.is_absolute():
            raise ValueError('Absolute path required')

        return value


CPPythonPluginData = NewType('CPPythonPluginData', CPPythonData)


class SyncData(CPPythonModel):
    """Data that passes in a plugin sync"""

    provider_name: TypeName


class SupportedFeatures(CPPythonModel):
    """Plugin feature support"""

    initialization: Annotated[
        bool, Field(description='Whether the plugin supports initialization from an empty state')
    ] = False


class Information(CPPythonModel):
    """Plugin information that complements the packaged project metadata"""


class PluginGroupData(CPPythonModel, extra='forbid'):
    """Plugin group data"""

    root_directory: Annotated[DirectoryPath, Field(description='The directory of the project')]
    tool_directory: Annotated[
        Path,
        Field(
            description=(
                'Points to the project plugin directory within the tool directory. '
                'This directory is for project specific cached data.'
            )
        ),
    ]


class Plugin(SynodicPlugin, Protocol):
    """CPPython plugin"""

    @abstractmethod
    def __init__(self, group_data: PluginGroupData) -> None:
        """Initializes the plugin"""
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
        """Initializes the data plugin"""
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def features(directory: DirectoryPath) -> SupportedFeatures:
        """Broadcasts the shared features of the data plugin to CPPython

        Args:
            directory: The root directory where features are evaluated

        Returns:
            The supported features - `SupportedDataFeatures`. Cast to this type to help us avoid generic typing
        """
        raise NotImplementedError

    @classmethod
    async def download_tooling(cls, directory: DirectoryPath) -> None:
        """Installs the external tooling required by the plugin. Should be overridden if required

        Args:
            directory: The directory to download any extra tooling to
        """


class CPPythonGlobalConfiguration(CPPythonModel, extra='forbid'):
    """Global data extracted by the tool"""

    current_check: Annotated[bool, Field(alias='current-check', description='Checks for a new CPPython version')] = True


ProviderData = NewType('ProviderData', dict[str, Any])
GeneratorData = NewType('GeneratorData', dict[str, Any])


class CPPythonLocalConfiguration(CPPythonModel, extra='forbid'):
    """Data required by the tool"""

    configuration_path: Annotated[
        Path | None,
        Field(
            description='The path to the configuration override file. If present, configuration found in the given'
            ' directory will be preferred'
        ),
    ] = None

    install_path: Annotated[
        Path,
        Field(
            alias='install-path',
            description='The global install path for the project. Provider and generator plugins will be'
            ' installed here.',
        ),
    ] = Path.home() / '.cppython'

    tool_path: Annotated[
        Path,
        Field(
            alias='tool-path',
            description='The local tooling path for the project. If the provider or generator need additional file'
            ' support, this directory will be used',
        ),
    ] = Path('tool')

    build_path: Annotated[
        Path,
        Field(
            alias='build-path',
            description='The local build path for the project. This is where the artifacts of the local C++ build'
            ' process will be generated.',
        ),
    ] = Path('build')

    provider: Annotated[ProviderData, Field(description="Provider plugin data associated with 'provider_name")] = (
        ProviderData({})
    )

    provider_name: Annotated[
        TypeName | None,
        Field(
            alias='provider-name',
            description='If empty, the provider will be automatically deduced.',
        ),
    ] = None

    generator: Annotated[GeneratorData, Field(description="Generator plugin data associated with 'generator_name'")] = (
        GeneratorData({})
    )

    generator_name: Annotated[
        TypeName | None,
        Field(
            alias='generator-name',
            description='If empty, the generator will be automatically deduced.',
        ),
    ] = None

    dependencies: Annotated[
        list[str] | None,
        Field(
            description='A list of dependencies that will be installed. This is a list of pip compatible requirements'
            ' strings',
        ),
    ] = None


class ToolData(CPPythonModel):
    """Tool entry of pyproject.toml"""

    cppython: Annotated[CPPythonLocalConfiguration | None, Field(description='CPPython tool data')] = None


class PyProject(CPPythonModel):
    """pyproject.toml schema"""

    project: Annotated[PEP621Configuration, Field(description='PEP621: https://www.python.org/dev/peps/pep-0621/')]
    tool: Annotated[ToolData | None, Field(description='Tool data')] = None


class CoreData(CPPythonModel):
    """Core resolved data that will be resolved"""

    project_data: ProjectData
    cppython_data: CPPythonData


@runtime_checkable
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
