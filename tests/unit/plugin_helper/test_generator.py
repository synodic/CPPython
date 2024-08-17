"""Tests the integration test plugin"""

from typing import Any

import pytest

from pytest_cppython.mock.generator import MockGenerator
from pytest_cppython.tests import GeneratorUnitTests


class TestCPPythonGenerator(GeneratorUnitTests[MockGenerator]):
    """The tests for the Mock generator"""

    @pytest.fixture(name="plugin_data", scope="session")
    def fixture_plugin_data(self) -> dict[str, Any]:
        """Returns mock data

        Returns:
            An overridden data instance
        """

        return {}

    @pytest.fixture(name="plugin_type", scope="session")
    def fixture_plugin_type(self) -> type[MockGenerator]:
        """A required testing hook that allows type generation

        Returns:
            An overridden generator type
        """
        return MockGenerator
