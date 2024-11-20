"""Git SCM plugin"""

from pathlib import Path

from dulwich.errors import NotGitRepository
from dulwich.repo import Repo

from cppython.core.plugin_schema.scm import (
    SCM,
    SCMPluginGroupData,
    SupportedSCMFeatures,
)
from cppython.core.schema import Information


class GitSCM(SCM):
    """Git implementation hooks"""

    def __init__(self, group_data: SCMPluginGroupData) -> None:
        """Initializes the plugin"""
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

    @staticmethod
    def version(_: Path) -> str:
        """Extracts the system's version metadata

        Returns:
            The git version
        """
        return ''

    @staticmethod
    def description() -> str | None:
        """Requests extraction of the project description"""
        return None
