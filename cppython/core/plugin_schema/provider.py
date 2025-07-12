"""Provider data plugin definitions"""

from abc import abstractmethod
from typing import Any, Protocol, runtime_checkable

from pydantic.types import DirectoryPath

from cppython.core.plugin_schema.generator import SyncConsumer
from cppython.core.schema import (
    CorePluginData,
    DataPlugin,
    DataPluginGroupData,
    SupportedDataFeatures,
    SupportedFeatures,
    SyncData,
)


class ProviderPluginGroupData(DataPluginGroupData):
    """Base class for the configuration data that is set by the project for the provider"""


class SupportedProviderFeatures(SupportedDataFeatures):
    """Provider plugin feature support"""


class SyncProducer(Protocol):
    """Interface for producing synchronization data with generators"""

    @staticmethod
    @abstractmethod
    def supported_sync_type(sync_type: type[SyncData]) -> bool:
        """Queries for support for a given synchronization type

        Args:
            sync_type: The type to query support for

        Returns:
            Support
        """
        raise NotImplementedError

    @abstractmethod
    def sync_data(self, consumer: SyncConsumer) -> SyncData | None:
        """Requests generator information from the provider.

        The generator is either defined by a provider specific file or the CPPython configuration table

        Args:
            consumer: The consumer

        Returns:
            An instantiated data type, or None if no instantiation is made
        """
        raise NotImplementedError


@runtime_checkable
class Provider(DataPlugin, SyncProducer, Protocol):
    """Abstract type to be inherited by CPPython Provider plugins"""

    @abstractmethod
    def __init__(
        self, group_data: ProviderPluginGroupData, core_data: CorePluginData, configuration_data: dict[str, Any]
    ) -> None:
        """Initializes the provider"""
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def features(directory: DirectoryPath) -> SupportedFeatures:
        """Broadcasts the shared features of the Provider plugin to CPPython

        Args:
            directory: The root directory where features are evaluated

        Returns:
            The supported features - `SupportedProviderFeatures`. Cast to this type to help us avoid generic typing
        """
        raise NotImplementedError

    @abstractmethod
    def install(self) -> None:
        """Called when dependencies need to be installed from a lock file."""
        raise NotImplementedError

    @abstractmethod
    def update(self) -> None:
        """Called when dependencies need to be updated and written to the lock file."""
        raise NotImplementedError

    @abstractmethod
    def publish(self) -> None:
        """Called when the project needs to be published."""
        raise NotImplementedError
