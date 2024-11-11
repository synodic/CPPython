"""Pytest fixtures for Synodic tests"""

from pathlib import Path

import pytest


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
