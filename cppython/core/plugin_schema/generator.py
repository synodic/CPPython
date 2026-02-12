"""Generator data plugin definitions"""

from abc import abstractmethod
from typing import Any, Protocol, runtime_checkable

from pydantic.types import DirectoryPath

from cppython.core.schema import (
    CorePluginData,
    DataPlugin,
    DataPluginGroupData,
    SupportedDataFeatures,
    SupportedFeatures,
    SyncData,
)


class GeneratorPluginGroupData(DataPluginGroupData):
    """Base class for the configuration data that is set by the project for the generator"""


class SupportedGeneratorFeatures(SupportedDataFeatures):
    """Generator plugin feature support"""


class SyncConsumer(Protocol):
    """Interface for consuming synchronization data from providers"""

    @staticmethod
    @abstractmethod
    def sync_types() -> list[type[SyncData]]:
        """Broadcasts supported types

        Returns:
            A list of synchronization types that are supported
        """
        raise NotImplementedError

    @abstractmethod
    def sync(self, sync_data: SyncData) -> None:
        """Synchronizes generator files and state with the providers input

        Args:
            sync_data: The input data to sync with
        """
        raise NotImplementedError


@runtime_checkable
class Generator(DataPlugin, SyncConsumer, Protocol):
    """Abstract type to be inherited by CPPython Generator plugins"""

    @abstractmethod
    def __init__(
        self, group_data: GeneratorPluginGroupData, core_data: CorePluginData, configuration_data: dict[str, Any]
    ) -> None:
        """Initializes the generator plugin"""
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def features(directory: DirectoryPath) -> SupportedFeatures:
        """Broadcasts the shared features of the generator plugin to CPPython

        Args:
            directory: The root directory where features are evaluated

        Returns:
            The supported features - `SupportedGeneratorFeatures`. Cast to this type to help us avoid generic typing
        """
        raise NotImplementedError

    @abstractmethod
    def build(self, configuration: str | None = None) -> None:
        """Builds the project using the generator's build system.

        Executes the build step. The interpretation of ``configuration`` is
        generator-specific (e.g. CMake preset name, Meson build directory).

        Args:
            configuration: Optional named configuration override.
        """
        raise NotImplementedError

    @abstractmethod
    def test(self, configuration: str | None = None) -> None:
        """Runs tests using the generator's build system.

        Args:
            configuration: Optional named configuration override.
        """
        raise NotImplementedError

    @abstractmethod
    def bench(self, configuration: str | None = None) -> None:
        """Runs benchmarks using the generator's build system.

        Args:
            configuration: Optional named configuration override.
        """
        raise NotImplementedError

    @abstractmethod
    def run(self, target: str, configuration: str | None = None) -> None:
        """Runs a built executable by target name.

        Args:
            target: The name of the build target/executable to run.
            configuration: Optional named configuration override.
        """
        raise NotImplementedError
