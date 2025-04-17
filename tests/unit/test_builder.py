"""Tests the Builder and Resolver types"""

import logging
from importlib import metadata

from pytest_mock import MockerFixture

from cppython.builder import Builder, Resolver
from cppython.core.schema import (
    CPPythonLocalConfiguration,
    PEP621Configuration,
    ProjectConfiguration,
    ProjectData,
)
from cppython.test.mock.generator import MockGenerator
from cppython.test.mock.provider import MockProvider
from cppython.test.mock.scm import MockSCM


class TestBuilder:
    """Various tests for the Builder type"""

    @staticmethod
    def test_build(
        project_configuration: ProjectConfiguration,
        pep621_configuration: PEP621Configuration,
        cppython_local_configuration: CPPythonLocalConfiguration,
        mocker: MockerFixture,
    ) -> None:
        """Verifies that the builder can build a project with all test variants

        Args:
            project_configuration: Variant fixture for the project configuration
            pep621_configuration: Variant fixture for PEP 621 configuration
            cppython_local_configuration: Variant fixture for cppython configuration
            mocker: Pytest mocker fixture
        """
        logger = logging.getLogger()
        builder = Builder(project_configuration, logger)

        # Insert ourself into the builder and load the mock plugins by returning them directly in the expected order
        #   they will be built
        mocker.patch(
            'cppython.builder.entry_points',
            return_value=[metadata.EntryPoint(name='mock', value='mock', group='mock')],
        )
        mocker.patch.object(metadata.EntryPoint, 'load', side_effect=[MockGenerator, MockProvider, MockSCM])

        assert builder.build(pep621_configuration, cppython_local_configuration)


class TestResolver:
    """Various tests for the Resolver type"""

    @staticmethod
    def test_generate_plugins(
        project_configuration: ProjectConfiguration,
        cppython_local_configuration: CPPythonLocalConfiguration,
        project_data: ProjectData,
    ) -> None:
        """Verifies that the resolver can generate plugins

        Args:
            project_configuration: Variant fixture for the project configuration
            cppython_local_configuration: Variant fixture for cppython configuration
            project_data: Variant fixture for the project data
        """
        logger = logging.getLogger()
        resolver = Resolver(project_configuration, logger)

        assert resolver.generate_plugins(cppython_local_configuration, project_data)
