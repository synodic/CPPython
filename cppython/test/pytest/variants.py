"""Data definitions"""

from collections.abc import Sequence
from pathlib import Path

from cppython.core.plugin_schema.generator import Generator
from cppython.core.plugin_schema.provider import Provider
from cppython.core.plugin_schema.scm import SCM
from cppython.core.schema import (
    CPPythonGlobalConfiguration,
    CPPythonLocalConfiguration,
    PEP621Configuration,
    ProjectConfiguration,
)
from cppython.test.mock.generator import MockGenerator
from cppython.test.mock.provider import MockProvider
from cppython.test.mock.scm import MockSCM


def _pep621_configuration_list() -> list[PEP621Configuration]:
    """Creates a list of mocked configuration types

    Returns:
        A list of variants to test
    """
    variants = []

    # Default
    variants.append(PEP621Configuration(name='default-test', version='1.0.0'))

    return variants


def _cppython_local_configuration_list() -> list[CPPythonLocalConfiguration]:
    """Mocked list of local configuration data

    Returns:
        A list of variants to test
    """
    variants = []

    # Default
    variants.append(CPPythonLocalConfiguration())

    return variants


def _cppython_global_configuration_list() -> list[CPPythonGlobalConfiguration]:
    """Mocked list of global configuration data

    Returns:
        A list of variants to test
    """
    variants = []

    data = {'current-check': False}

    # Default
    variants.append(CPPythonGlobalConfiguration())

    # Check off
    variants.append(CPPythonGlobalConfiguration(**data))

    return variants


def _project_configuration_list() -> list[ProjectConfiguration]:
    """Mocked list of project configuration data

    Returns:
        A list of variants to test
    """
    variants = []

    # NOTE: pyproject_file will be overridden by fixture

    # Default
    variants.append(ProjectConfiguration(pyproject_file=Path('pyproject.toml'), version='0.1.0'))

    return variants


def _mock_provider_list() -> Sequence[type[Provider]]:
    """Mocked list of providers

    Returns:
        A list of mock providers
    """
    variants = []

    # Default
    variants.append(MockProvider)

    return variants


def _mock_generator_list() -> Sequence[type[Generator]]:
    """Mocked list of generators

    Returns:
        List of mock generators
    """
    variants = []

    # Default
    variants.append(MockGenerator)

    return variants


def _mock_scm_list() -> Sequence[type[SCM]]:
    """Mocked list of SCMs

    Returns:
        List of mock SCMs
    """
    variants = []

    # Default
    variants.append(MockSCM)

    return variants


pep621_variants = _pep621_configuration_list()
cppython_local_variants = _cppython_local_configuration_list()
cppython_global_variants = _cppython_global_configuration_list()
project_variants = _project_configuration_list()
provider_variants = _mock_provider_list()
generator_variants = _mock_generator_list()
scm_variants = _mock_scm_list()
