"""Git SCM plugin"""

from pathlib import Path

from cppython_core.plugin_schema.scm import (
    SCM,
    SCMPluginGroupData,
    SupportedSCMFeatures,
)
from cppython_core.schema import Information
from dulwich.errors import NotGitRepository
from dulwich.repo import Repo


class GitSCM(SCM):
    """Git implementation hooks"""

    def __init__(self, group_data: SCMPluginGroupData) -> None:
        self.group_data = group_data

    @staticmethod
    def features(directory: Path) -> SupportedSCMFeatures:
        """Broadcasts the shared features of the SCM plugin to CPPython

        Args:
            directory: The root directory where features are evaluated

        Returns:
            The supported features
        """

        is_repository = True
        try:
            Repo(str(directory))
        except NotGitRepository:
            is_repository = False

        return SupportedSCMFeatures(repository=is_repository)

    @staticmethod
    def information() -> Information:
        """Extracts the system's version metadata

        Returns:
            A version
        """
        return Information()

    def version(self, directory: Path) -> str:
        """Extracts the system's version metadata

        Args:
            directory: The repository path

        Returns:
            The git version
        """
        return ""

    def description(self) -> str | None:
        """Requests extraction of the project description"""
        return None
