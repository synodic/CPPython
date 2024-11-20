"""Mock SCM definitions"""

from pydantic import DirectoryPath

from cppython.core.plugin_schema.scm import (
    SCM,
    SCMPluginGroupData,
    SupportedSCMFeatures,
)
from cppython.core.schema import Information


class MockSCM(SCM):
    """A mock generator class for behavior testing"""

    def __init__(self, group_data: SCMPluginGroupData) -> None:
        """Initializes the mock generator"""
        self.group_data = group_data

    @staticmethod
    def features(_: DirectoryPath) -> SupportedSCMFeatures:
        """Broadcasts the shared features of the SCM plugin to CPPython

        Returns:
            The supported features
        """
        return SupportedSCMFeatures(repository=True)

    @staticmethod
    def information() -> Information:
        """Returns plugin information

        Returns:
            The plugin information
        """
        return Information()

    @staticmethod
    def version(_: DirectoryPath) -> str:
        """Extracts the system's version metadata

        Returns:
            A version
        """
        return '1.0.0'
