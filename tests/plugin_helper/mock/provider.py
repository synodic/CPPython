"""Mock provider definitions"""

from typing import Any

from cppython_core.plugin_schema.generator import SyncConsumer
from cppython_core.plugin_schema.provider import (
    Provider,
    ProviderPluginGroupData,
    SupportedProviderFeatures,
)
from cppython_core.schema import CorePluginData, CPPythonModel, Information, SyncData
from pydantic import DirectoryPath

from pytest_cppython.mock.generator import MockSyncData


class MockProviderData(CPPythonModel):
    """Dummy data"""


class MockProvider(Provider):
    """A mock provider class for behavior testing"""

    downloaded: DirectoryPath | None = None

    def __init__(
        self, group_data: ProviderPluginGroupData, core_data: CorePluginData, configuration_data: dict[str, Any]
    ) -> None:
        self.group_data = group_data
        self.core_data = core_data
        self.configuration_data = MockProviderData(**configuration_data)

    @staticmethod
    def features(directory: DirectoryPath) -> SupportedProviderFeatures:
        """Broadcasts the shared features of the Provider plugin to CPPython

        Args:
            directory: The root directory where features are evaluated

        Returns:
            The supported features
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
        cls.downloaded = directory

    def install(self) -> None:
        pass

    def update(self) -> None:
        pass
