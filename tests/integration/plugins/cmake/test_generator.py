"""Integration tests for the provider"""

from typing import Any

import pytest

from cppython.plugins.cmake.plugin import CMakeGenerator
from cppython.plugins.cmake.schema import CMakeConfiguration
from cppython.test.pytest.contracts import GeneratorIntegrationTestContract

pytest_plugins = ['tests.fixtures.cmake']


class TestCPPythonGenerator(GeneratorIntegrationTestContract[CMakeGenerator]):
    """The tests for the CMake generator"""

    @staticmethod
    @pytest.fixture(name='plugin_data', scope='session')
    def fixture_plugin_data(cmake_data: CMakeConfiguration) -> dict[str, Any]:
        """A required testing hook that allows data generation

        Args:
            cmake_data: The input data

        Returns:
            The constructed plugin data
        """
        return cmake_data.model_dump()

    @staticmethod
    @pytest.fixture(name='plugin_type', scope='session')
    def fixture_plugin_type() -> type[CMakeGenerator]:
        """A required testing hook that allows type generation

        Returns:
            The type of the Generator
        """
        return CMakeGenerator
