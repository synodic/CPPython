"""Tests the integration test plugin"""

from typing import Any

import pytest

from tests.plugin_helper.mock.scm import MockSCM
from tests.plugin_helper.tests import SCMIntegrationTests


class TestCPPythonSCM(SCMIntegrationTests[MockSCM]):
    """The tests for the Mock version control"""

    @pytest.fixture(name="plugin_data", scope="session")
    def fixture_plugin_data(self) -> dict[str, Any]:
        """Returns mock data

        Returns:
            An overridden data instance
        """

        return {}

    @pytest.fixture(name="plugin_type", scope="session")
    def fixture_plugin_type(self) -> type[MockSCM]:
        """A required testing hook that allows type generation

        Returns:
            An overridden version control type
        """
        return MockSCM
