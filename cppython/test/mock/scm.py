"""Mock SCM definitions"""

from pydantic import DirectoryPath

from cppython.core.plugin_schema.scm import (
    SCM,
    SCMPluginGroupData,
    SupportedSCMFeatures,
)
from cppython.core.schema import Information, SupportedFeatures


class MockSCM(SCM):
    """A mock generator class for behavior testing"""

    def __init__(self, group_data: SCMPluginGroupData) -> None:
        """Initializes the mock generator"""
        self.group_data = group_data

    @staticmethod
    def features(directory: DirectoryPath) -> SupportedFeatures:
        """Broadcasts the shared features of the SCM plugin to CPPython

        Args:
            directory: The root directory where features are evaluated

        Returns:
            The supported features - `SupportedSCMFeatures`. Cast to this type to help us avoid generic typing
        """
        return SupportedSCMFeatures(repository=True)

    @staticmethod
    def information() -> Information:
        """Returns plugin information

        Returns:
            The plugin information
        """
        return Information()

    def version(self, directory: DirectoryPath) -> str:
        """Extracts the system's version metadata

        Args:
            directory: The input directory

        Returns:
            A version
        """
        return '1.0.0'
