"""Version control data plugin definitions"""

from abc import abstractmethod
from typing import Annotated, Protocol, runtime_checkable

from pydantic import DirectoryPath, Field

from cppython.core.schema import Plugin, PluginGroupData, SupportedFeatures


class SCMPluginGroupData(PluginGroupData):
    """SCM plugin input data"""


class SupportedSCMFeatures(SupportedFeatures):
    """SCM plugin feature support"""

    repository: Annotated[
        bool, Field(description='True if the directory is a repository for the SCM. False, otherwise')
    ]


@runtime_checkable
class SCM(Plugin, Protocol):
    """Base class for version control systems"""

    @abstractmethod
    def __init__(self, group_data: SCMPluginGroupData) -> None:
        """Initializes the SCM plugin"""
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def features(directory: DirectoryPath) -> SupportedFeatures:
        """Broadcasts the shared features of the SCM plugin to CPPython

        Args:
            directory: The root directory where features are evaluated

        Returns:
            The supported features - `SupportedSCMFeatures`. Cast to this type to help us avoid generic typing
        """
        raise NotImplementedError

    @abstractmethod
    def version(self, directory: DirectoryPath) -> str:
        """Extracts the system's version metadata

        Args:
            directory: The input directory

        Returns:
            A version string
        """
        raise NotImplementedError

    def description(self) -> str | None:
        """Requests extraction of the project description

        Returns:
            Returns the project description, or none if unavailable
        """
