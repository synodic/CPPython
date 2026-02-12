"""Fixtures for the meson plugin"""

from pathlib import Path
from typing import cast

import pytest

from cppython.plugins.meson.schema import MesonConfiguration


def _meson_data_list() -> list[MesonConfiguration]:
    """Creates a list of mocked configuration types.

    Returns:
        A list of variants to test
    """
    # Default
    default = MesonConfiguration()

    # Non-root build file
    config = MesonConfiguration(build_file=Path('subdir/meson.build'), build_directory='custom-builddir')

    return [default, config]


@pytest.fixture(
    name='meson_data',
    scope='session',
    params=_meson_data_list(),
)
def fixture_meson_data(request: pytest.FixtureRequest) -> MesonConfiguration:
    """A fixture to provide a list of configuration types.

    Args:
        request: Parameterization list

    Returns:
        A configuration type instance
    """
    return cast(MesonConfiguration, request.param)
