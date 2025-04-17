"""Shared definitions for testing."""

from typing import Any

from pydantic import DirectoryPath

from cppython.core.plugin_schema.generator import (
    Generator,
    GeneratorPluginGroupData,
    SupportedGeneratorFeatures,
)
from cppython.core.schema import CorePluginData, CPPythonModel, Information, SupportedFeatures, SyncData


class MockSyncData(SyncData):
    """A Mock data type"""


class MockGeneratorData(CPPythonModel):
    """Dummy data"""


class MockGenerator(Generator):
    """A mock generator class for behavior testing"""

    def __init__(
        self, group_data: GeneratorPluginGroupData, core_data: CorePluginData, configuration_data: dict[str, Any]
    ) -> None:
        """Initializes the mock generator"""
        self.group_data = group_data
        self.core_data = core_data
        self.configuration_data = MockGeneratorData(**configuration_data)

    @staticmethod
    def features(directory: DirectoryPath) -> SupportedFeatures:
        """Broadcasts the shared features of the generator plugin to CPPython

        Returns:
            The supported features - `SupportedGeneratorFeatures`. Cast to this type to help us avoid generic typing
        """
        return SupportedGeneratorFeatures()

    @staticmethod
    def information() -> Information:
        """Returns plugin information

        Returns:
            The plugin information
        """
        return Information()

    @staticmethod
    def sync_types() -> list[type[SyncData]]:
        """Returns the supported synchronization data types for the mock generator.

        Returns:
            A list of supported synchronization data types.
        """
        return [MockSyncData]

    def sync(self, sync_data: SyncData) -> None:
        """Synchronizes generator files and state with the providers input"""
