"""Data variations for testing"""

# from pathlib import Path
from pathlib import Path
from typing import cast

import pytest

from cppython.plugins.cmake.schema import CMakeConfiguration


def _cmake_data_list() -> list[CMakeConfiguration]:
    """Creates a list of mocked configuration types

    Returns:
        A list of variants to test
    """
    variants = []

    # Default
    variants.append(CMakeConfiguration(configuration_name="default"))

    # variants.append(CMakeConfiguration(preset_file=Path("inner/CMakePresets.json"), configuration_name="default"))

    return variants


@pytest.fixture(
    name="cmake_data",
    scope="session",
    params=_cmake_data_list(),
)
def fixture_cmake_data(request: pytest.FixtureRequest) -> CMakeConfiguration:
    """A fixture to provide a list of configuration types

    Args:
        request: Parameterization list

    Returns:
        A configuration type instance
    """

    return cast(CMakeConfiguration, request.param)


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Called for each test function

    Args:
        metafunc: Pytest hook data
    """

    for fixture in metafunc.fixturenames:
        match fixture.split("_", 1):
            case ["internal", "plugin_data_path"]:
                # There should only ever be one fixture named 'internal_plugin_data_path' for value caching
                data_path = metafunc.config.rootpath / "tests" / "data"

                test_paths: list[Path | None] = []

                for path in data_path.glob("*"):
                    if path.is_dir():
                        test_paths.append(path)

                if not test_paths:
                    test_paths = [None]
                metafunc.parametrize(fixture, test_paths, scope="session")

            case ["internal", "data_path"]:
                # There should only ever be one fixture named 'internal_data_path' for value caching
                data_path = Path(__file__).parent / "data"
                metafunc.parametrize(fixture, list(data_path.glob("*")), scope="session")

            case ["build", directory]:
                data_path = metafunc.config.rootpath / "tests" / "build" / directory
                metafunc.parametrize(fixture, [data_path], scope="session")
