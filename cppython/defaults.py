"""Defines a SCM subclass that is used as the default SCM if no plugin is found or selected"""

from pydantic import DirectoryPath

from cppython.core.plugin_schema.scm import (
    SCM,
    SCMPluginGroupData,
    SupportedSCMFeatures,
)
from cppython.core.schema import Information, SupportedFeatures


class DefaultSCM(SCM):
    """A default SCM class for when no SCM plugin is selected"""

    def __init__(self, group_data: SCMPluginGroupData) -> None:
        """Initializes the default SCM class"""
        self.group_data = group_data

    @staticmethod
    def features(directory: DirectoryPath) -> SupportedFeatures:
        """Broadcasts the shared features of the SCM plugin to CPPython

        Returns:
            The supported features - `SupportedGeneratorFeatures`. Cast to this type to help us avoid generic typing
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
    def version(directory: DirectoryPath) -> str:
        """Extracts the system's version metadata

        Returns:
            A version
        """
        return '1.0.0'
