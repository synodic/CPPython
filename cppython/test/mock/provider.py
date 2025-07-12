"""Mock provider definitions"""

from typing import Any

from pydantic import DirectoryPath

from cppython.core.plugin_schema.generator import SyncConsumer
from cppython.core.plugin_schema.provider import (
    Provider,
    ProviderPluginGroupData,
    SupportedProviderFeatures,
)
from cppython.core.schema import CorePluginData, CPPythonModel, Information, SupportedFeatures, SyncData
from cppython.test.mock.generator import MockSyncData


class MockProviderData(CPPythonModel):
    """Dummy data"""


class MockProvider(Provider):
    """A mock provider class for behavior testing"""

    downloaded: DirectoryPath | None = None

    def __init__(
        self, group_data: ProviderPluginGroupData, core_data: CorePluginData, configuration_data: dict[str, Any]
    ) -> None:
        """Initializes the mock provider"""
        self.group_data = group_data
        self.core_data = core_data
        self.configuration_data = MockProviderData(**configuration_data)

    @staticmethod
    def features(directory: DirectoryPath) -> SupportedFeatures:
        """Broadcasts the shared features of the Provider plugin to CPPython

        Returns:
            The supported features - `SupportedProviderFeatures`. Cast to this type to help us avoid generic typing
        """
        return SupportedProviderFeatures()

    @staticmethod
    def information() -> Information:
        """Returns plugin information

        Returns:
            The plugin information
        """
        return Information()

    @staticmethod
    def supported_sync_type(sync_type: type[SyncData]) -> bool:
        """Broadcasts supported types

        Args:
            sync_type: The input type

        Returns:
            Support
        """
        return sync_type == MockSyncData

    def sync_data(self, consumer: SyncConsumer) -> SyncData | None:
        """Gathers synchronization data

        Args:
            consumer: The input consumer

        Returns:
            The sync data object
        """
        # This is a mock class, so any generator sync type is OK
        for sync_type in consumer.sync_types():
            match sync_type:
                case underlying_type if underlying_type is MockSyncData:
                    return MockSyncData(provider_name=self.name())

        return None

    @classmethod
    async def download_tooling(cls, directory: DirectoryPath) -> None:
        """Downloads the provider tooling"""
        cls.downloaded = directory

    def install(self) -> None:
        """Installs the provider"""
        pass

    def update(self) -> None:
        """Updates the provider"""
        pass

    def publish(self) -> None:
        """Updates the provider"""
        pass
