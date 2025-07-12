"""Tests the unit test plugin"""

from typing import Any

import pytest

from cppython.test.mock.scm import MockSCM
from cppython.test.pytest.contracts import SCMTestContract


class TestCPPythonSCM(SCMTestContract[MockSCM]):
    """The tests for the Mock version control"""

    @staticmethod
    @pytest.fixture(name='plugin_data', scope='session')
    def fixture_plugin_data() -> dict[str, Any]:
        """Returns mock data

        Returns:
            An overridden data instance
        """
        return {}

    @staticmethod
    @pytest.fixture(name='plugin_type', scope='session')
    def fixture_plugin_type() -> type[MockSCM]:
        """A required testing hook that allows type generation

        Returns:
            An overridden version control type
        """
        return MockSCM
