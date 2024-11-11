"""Data variations for testing"""

# from pathlib import Path
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
