"""Integration tests for the cppython SCM plugin"""

import pytest

from cppython.plugins.git.plugin import GitSCM
from cppython.test.pytest.contracts import SCMIntegrationTestContract


class TestGitInterface(SCMIntegrationTestContract[GitSCM]):
    """Integration tests for the Git SCM plugin"""

    @staticmethod
    @pytest.fixture(name='plugin_type', scope='session')
    def fixture_plugin_type() -> type[GitSCM]:
        """A required testing hook that allows type generation

        Returns:
            The SCM type
        """
        return GitSCM
