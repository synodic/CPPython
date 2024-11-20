"""Shared definitions for testing."""

from typing import Any

from pydantic import DirectoryPath

from cppython.core.plugin_schema.generator import (
    Generator,
    GeneratorPluginGroupData,
    SupportedGeneratorFeatures,
)
from cppython.core.schema import CorePluginData, CPPythonModel, Information, SyncData


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
    def features(_: DirectoryPath) -> SupportedGeneratorFeatures:
        """Broadcasts the shared features of the generator plugin to CPPython

        Returns:
            The supported features
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
        """_summary_

        Returns:
            _description_
        """
        return [MockSyncData]

    def sync(self, _: SyncData) -> None:
        """Synchronizes generator files and state with the providers input"""
