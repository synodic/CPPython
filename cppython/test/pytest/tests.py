"""Types to inherit from"""

import asyncio
from abc import ABCMeta
from pathlib import Path

import pytest

from cppython.core.plugin_schema.generator import Generator
from cppython.core.plugin_schema.provider import Provider
from cppython.core.plugin_schema.scm import SCM
from cppython.test.pytest.shared import (
    DataPluginIntegrationTests,
    DataPluginUnitTests,
    GeneratorTests,
    PluginIntegrationTests,
    PluginUnitTests,
    ProviderTests,
    SCMTests,
)
from cppython.utility.utility import canonicalize_type


class ProviderIntegrationTests[T: Provider](DataPluginIntegrationTests[T], ProviderTests[T], metaclass=ABCMeta):
    """Base class for all provider integration tests that test plugin agnostic behavior"""

    @staticmethod
    @pytest.fixture(autouse=True, scope='session')
    def _fixture_install_dependency(plugin: T, install_path: Path) -> None:
        """Forces the download to only happen once per test session"""
        path = install_path / canonicalize_type(type(plugin)).name
        path.mkdir(parents=True, exist_ok=True)

        asyncio.run(plugin.download_tooling(path))

    @staticmethod
    def test_install(plugin: T) -> None:
        """Ensure that the vanilla install command functions

        Args:
            plugin: A newly constructed provider
        """
        plugin.install()

    @staticmethod
    def test_update(plugin: T) -> None:
        """Ensure that the vanilla update command functions

        Args:
            plugin: A newly constructed provider
        """
        plugin.update()

    @staticmethod
    def test_group_name(plugin_type: type[T]) -> None:
        """Verifies that the group name is the same as the plugin type

        Args:
            plugin_type: The type to register
        """
        assert canonicalize_type(plugin_type).group == 'provider'


class ProviderUnitTests[T: Provider](DataPluginUnitTests[T], ProviderTests[T], metaclass=ABCMeta):
    """Base class for all provider unit tests that test plugin agnostic behavior.

    Custom implementations of the Provider class should inherit from this class for its tests.
    """


class GeneratorIntegrationTests[T: Generator](DataPluginIntegrationTests[T], GeneratorTests[T], metaclass=ABCMeta):
    """Base class for all scm integration tests that test plugin agnostic behavior"""

    @staticmethod
    def test_group_name(plugin_type: type[T]) -> None:
        """Verifies that the group name is the same as the plugin type

        Args:
            plugin_type: The type to register
        """
        assert canonicalize_type(plugin_type).group == 'generator'


class GeneratorUnitTests[T: Generator](DataPluginUnitTests[T], GeneratorTests[T], metaclass=ABCMeta):
    """Base class for all Generator unit tests that test plugin agnostic behavior.

    Custom implementations of the Generator class should inherit from this class for its tests.
    """


class SCMIntegrationTests[T: SCM](PluginIntegrationTests[T], SCMTests[T], metaclass=ABCMeta):
    """Base class for all generator integration tests that test plugin agnostic behavior"""

    @staticmethod
    def test_group_name(plugin_type: type[T]) -> None:
        """Verifies that the group name is the same as the plugin type

        Args:
            plugin_type: The type to register
        """
        assert canonicalize_type(plugin_type).group == 'scm'


class SCMUnitTests[T: SCM](PluginUnitTests[T], SCMTests[T], metaclass=ABCMeta):
    """Base class for all Generator unit tests that test plugin agnostic behavior.

    Custom implementations of the Generator class should inherit from this class for its tests.
    """
