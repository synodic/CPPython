"""Tests the integration test plugin"""

from typing import Any

import pytest

from cppython.test.mock.generator import MockGenerator
from cppython.test.pytest.contracts import GeneratorUnitTestContract


class TestCPPythonGenerator(GeneratorUnitTestContract[MockGenerator]):
    """The tests for the Mock generator"""

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
    def fixture_plugin_type() -> type[MockGenerator]:
        """A required testing hook that allows type generation

        Returns:
            An overridden generator type
        """
        return MockGenerator
