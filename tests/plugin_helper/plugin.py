"""Direct Fixtures"""

import shutil
from pathlib import Path
from typing import cast

import pytest

from cppython.core.plugin_schema.generator import Generator
from cppython.core.plugin_schema.provider import Provider
from cppython.core.plugin_schema.scm import SCM
from cppython.core.resolution import (
    PluginBuildData,
    PluginCPPythonData,
    resolve_cppython,
    resolve_pep621,
    resolve_project_configuration,
)
from cppython.core.schema import (
    CoreData,
    CPPythonData,
    CPPythonGlobalConfiguration,
    CPPythonLocalConfiguration,
    PEP621Configuration,
    PEP621Data,
    ProjectConfiguration,
    ProjectData,
    PyProject,
    ToolData,
)
from tests.plugin_helper.variants import (
    cppython_global_variants,
    cppython_local_variants,
    pep621_variants,
    project_variants,
)


@pytest.fixture(
    name="install_path",
    scope="session",
)
def fixture_install_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Creates temporary install location
    Args:
        tmp_path_factory: Factory for centralized temporary directories
    Returns:
        A temporary directory
    """
    path = tmp_path_factory.getbasetemp()
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture(
    name="pep621_configuration",
    scope="session",
    params=pep621_variants,
)
def fixture_pep621_configuration(request: pytest.FixtureRequest) -> PEP621Configuration:
    """Fixture defining all testable variations of PEP621

    Args:
        request: Parameterization list

    Returns:
        PEP621 variant
    """

    return cast(PEP621Configuration, request.param)


@pytest.fixture(
    name="pep621_data",
    scope="session",
)
def fixture_pep621_data(
    pep621_configuration: PEP621Configuration, project_configuration: ProjectConfiguration
) -> PEP621Data:
    """Resolved project table fixture

    Args:
        pep621_configuration: The input configuration to resolve
        project_configuration: The project configuration to help with the resolve

    Returns:
        The resolved project table
    """

    return resolve_pep621(pep621_configuration, project_configuration, None)


@pytest.fixture(
    name="cppython_local_configuration",
    scope="session",
    params=cppython_local_variants,
)
def fixture_cppython_local_configuration(
    request: pytest.FixtureRequest, install_path: Path
) -> CPPythonLocalConfiguration:
    """Fixture defining all testable variations of CPPythonData

    Args:
        request: Parameterization list
        install_path: The temporary install directory

    Returns:
        Variation of CPPython data
    """
    cppython_local_configuration = cast(CPPythonLocalConfiguration, request.param)

    data = cppython_local_configuration.model_dump(by_alias=True)

    # Pin the install location to the base temporary directory
    data["install-path"] = install_path

    # Fill the plugin names with mocked values
    data["provider-name"] = "mock"
    data["generator-name"] = "mock"

    return CPPythonLocalConfiguration(**data)


@pytest.fixture(
    name="cppython_global_configuration",
    scope="session",
    params=cppython_global_variants,
)
def fixture_cppython_global_configuration(request: pytest.FixtureRequest) -> CPPythonGlobalConfiguration:
    """Fixture defining all testable variations of CPPythonData

    Args:
        request: Parameterization list

    Returns:
        Variation of CPPython data
    """
    cppython_global_configuration = cast(CPPythonGlobalConfiguration, request.param)

    return cppython_global_configuration


@pytest.fixture(
    name="plugin_build_data",
    scope="session",
)
def fixture_plugin_build_data(
    provider_type: type[Provider],
    generator_type: type[Generator],
    scm_type: type[SCM],
) -> PluginBuildData:
    """Fixture for constructing resolved CPPython table data

    Args:
        provider_type: The provider type
        generator_type: The generator type
        scm_type: The scm type

    Returns:
        The plugin build data
    """

    return PluginBuildData(generator_type=generator_type, provider_type=provider_type, scm_type=scm_type)


@pytest.fixture(
    name="plugin_cppython_data",
    scope="session",
)
def fixture_plugin_cppython_data(
    provider_type: type[Provider],
    generator_type: type[Generator],
    scm_type: type[SCM],
) -> PluginCPPythonData:
    """Fixture for constructing resolved CPPython table data

    Args:
        provider_type: The provider type
        generator_type: The generator type
        scm_type: The scm type

    Returns:
        The plugin data for CPPython resolution
    """

    return PluginCPPythonData(
        generator_name=generator_type.name(), provider_name=provider_type.name(), scm_name=scm_type.name()
    )


@pytest.fixture(
    name="cppython_data",
    scope="session",
)
def fixture_cppython_data(
    cppython_local_configuration: CPPythonLocalConfiguration,
    cppython_global_configuration: CPPythonGlobalConfiguration,
    project_data: ProjectData,
    plugin_cppython_data: PluginCPPythonData,
) -> CPPythonData:
    """Fixture for constructing resolved CPPython table data

    Args:
        cppython_local_configuration: The local configuration to resolve
        cppython_global_configuration: The global configuration to resolve
        project_data: The project data to help with the resolve
        plugin_cppython_data: Plugin data for CPPython resolution

    Returns:
        The resolved CPPython table
    """

    return resolve_cppython(
        cppython_local_configuration, cppython_global_configuration, project_data, plugin_cppython_data
    )


@pytest.fixture(
    name="core_data",
)
def fixture_core_data(cppython_data: CPPythonData, project_data: ProjectData) -> CoreData:
    """Fixture for creating the wrapper CoreData type

    Args:
        cppython_data: CPPython data
        project_data: The project data

    Returns:
        Wrapper Core Type
    """

    return CoreData(cppython_data=cppython_data, project_data=project_data)


@pytest.fixture(name="plugin_data_path", scope="session")
def fixture_plugin_data_path(internal_plugin_data_path: list[Path | None]) -> list[Path | None]:
    """Fixture cache of internal_plugin_data_path

    Args:
        internal_plugin_data_path: The input meta data

    Returns:
        The session scoped data
    """

    return internal_plugin_data_path


@pytest.fixture(name="data_path", scope="session")
def fixture_data_path(internal_data_path: list[Path]) -> list[Path]:
    """Fixture cache of internal_data_path

    Args:
        internal_data_path: The input meta data

    Returns:
        The session scoped data
    """

    return internal_data_path


@pytest.fixture(
    name="project_configuration",
    scope="session",
    params=project_variants,
)
def fixture_project_configuration(
    request: pytest.FixtureRequest,
    tmp_path_factory: pytest.TempPathFactory,
    data_path: Path,
    plugin_data_path: Path | None,
) -> ProjectConfiguration:
    """Project configuration fixture

    Args:
        request: Parameterized configuration data
        tmp_path_factory: Factory for centralized temporary directories
        data_path: Project file requirements
        plugin_data_path: Parameterized path to a data directory

    Returns:
        Configuration with temporary directory capabilities
    """

    tmp_path = tmp_path_factory.mktemp("workspace-")

    shutil.copytree(data_path, tmp_path, dirs_exist_ok=True)

    if plugin_data_path is not None:
        shutil.copytree(plugin_data_path, tmp_path, dirs_exist_ok=True)

    configuration = cast(ProjectConfiguration, request.param)

    # Pin the project location
    paths = list(tmp_path.rglob("pyproject.toml"))

    # 'paths' length guaranteed to be 1
    configuration.pyproject_file = paths[0].resolve()

    return configuration


@pytest.fixture(
    name="project_data",
    scope="session",
)
def fixture_project_data(project_configuration: ProjectConfiguration) -> ProjectData:
    """Fixture that creates a project space at 'workspace/test_project/pyproject.toml'
    Args:
        project_configuration: Project data
    Returns:
        A project data object that has populated a function level temporary directory
    """

    return resolve_project_configuration(project_configuration)


@pytest.fixture(name="project")
def fixture_project(
    cppython_local_configuration: CPPythonLocalConfiguration, pep621_configuration: PEP621Configuration
) -> PyProject:
    """Parameterized construction of PyProject data
    Args:
        cppython_local_configuration: The parameterized cppython table
        pep621_configuration: The project table
    Returns:
        All the data as one object
    """

    tool = ToolData(cppython=cppython_local_configuration)
    return PyProject(project=pep621_configuration, tool=tool)
