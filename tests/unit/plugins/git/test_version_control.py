"""Unit tests for the cppython SCM plugin"""

import pytest

from cppython.plugins.git.plugin import GitSCM
from cppython.test.pytest.tests import SCMUnitTests


class TestGitInterface(SCMUnitTests[GitSCM]):
    """Unit tests for the Git SCM plugin"""

    @pytest.fixture(name="plugin_type", scope="session")
    def fixture_plugin_type(self) -> type[GitSCM]:
        """A required testing hook that allows type generation

        Returns:
            The SCM type
        """
        return GitSCM
