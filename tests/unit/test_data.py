"""Tests the Data type"""

import logging

import pytest

from cppython.builder import Builder
from cppython.core.resolution import PluginBuildData
from cppython.core.schema import (
    CPPythonLocalConfiguration,
    PEP621Configuration,
    ProjectConfiguration,
)
from cppython.data import Data
from cppython.test.mock.generator import MockGenerator
from cppython.test.mock.provider import MockProvider
from cppython.test.mock.scm import MockSCM


class TestData:
    """Various tests for the Data type"""

    @staticmethod
    @pytest.fixture(
        name='data',
    )
    def fixture_data(
        project_configuration: ProjectConfiguration,
        pep621_configuration: PEP621Configuration,
        cppython_local_configuration: CPPythonLocalConfiguration,
    ) -> Data:
        """Creates a mock plugins fixture.

        We want all the plugins to use the same data variants at the same time, so we
        have to resolve data inside the fixture instead of using other data fixtures

        Args:
            project_configuration: Variant fixture for the project configuration
            pep621_configuration: Variant fixture for PEP 621 configuration
            cppython_local_configuration: Variant fixture for cppython configuration

        Returns:
            The mock plugins fixture

        """
        logger = logging.getLogger()
        builder = Builder(project_configuration, logger)

        plugin_build_data = PluginBuildData(generator_type=MockGenerator, provider_type=MockProvider, scm_type=MockSCM)

        return builder.build(pep621_configuration, cppython_local_configuration, plugin_build_data)

    @staticmethod
    def test_sync(data: Data) -> None:
        """Verifies that the sync method executes without error

        Args:
            data: Fixture for the mocked data class
        """
        data.sync()
