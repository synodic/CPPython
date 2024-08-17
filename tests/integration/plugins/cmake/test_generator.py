"""Integration tests for the provider"""

from typing import Any

import pytest
from pytest_cppython.tests import GeneratorIntegrationTests

from cppython_cmake.plugin import CMakeGenerator
from cppython_cmake.schema import CMakeConfiguration


class TestCPPythonGenerator(GeneratorIntegrationTests[CMakeGenerator]):
    """The tests for the CMake generator"""

    @pytest.fixture(name="plugin_data", scope="session")
    def fixture_plugin_data(self, cmake_data: CMakeConfiguration) -> dict[str, Any]:
        """A required testing hook that allows data generation

        Args:
            cmake_data: The input data

        Returns:
            The constructed plugin data
        """

        return cmake_data.model_dump()

    @pytest.fixture(name="plugin_type", scope="session")
    def fixture_plugin_type(self) -> type[CMakeGenerator]:
        """A required testing hook that allows type generation

        Returns:
            The type of the Generator
        """
        return CMakeGenerator
