"""Tests the Builder and Resolver types"""

import logging

import pytest_cppython

from cppython.builder import Builder, Resolver
from cppython.core.schema import (
    CPPythonLocalConfiguration,
    PEP621Configuration,
    ProjectConfiguration,
    ProjectData,
)


class TestBuilder:
    """Various tests for the Builder type"""

    def test_build(
        self,
        project_configuration: ProjectConfiguration,
        pep621_configuration: PEP621Configuration,
        cppython_local_configuration: CPPythonLocalConfiguration,
    ) -> None:
        """Verifies that the builder can build a project with all test variants

        Args:
            project_configuration: Variant fixture for the project configuration
            pep621_configuration: Variant fixture for PEP 621 configuration
            cppython_local_configuration: Variant fixture for cppython configuration
        """
        logger = logging.getLogger()
        builder = Builder(project_configuration, logger)

        assert builder.build(pep621_configuration, cppython_local_configuration)


class TestResolver:
    """Various tests for the Resolver type"""

    def test_generate_plugins(
        self,
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
