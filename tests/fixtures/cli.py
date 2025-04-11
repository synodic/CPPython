"""Fixtures for interfacing with the CLI."""

import os
import platform

import pytest
from typer.testing import CliRunner


@pytest.fixture(
    name='typer_runner',
    scope='session',
)
def fixture_typer_runner() -> CliRunner:
    """Returns a runner setup for the CPPython interface"""
    runner = CliRunner()

    return runner


@pytest.fixture(
    name='fresh_environment',
    scope='session',
)
def fixture_fresh_environment(request: pytest.FixtureRequest) -> dict[str, str]:
    """Create a fresh environment for subprocess calls."""
    # Start with a minimal environment
    new_env = {}

    # Copy only variables you need
    if platform.system() == 'Windows':
        new_env['SystemRoot'] = os.environ['SystemRoot']  # noqa: SIM112

    # Provide a PATH that doesn't contain venv references
    new_env['PATH'] = os.environ['PATH']

    # Set the Cppython root directory
    new_env['CPPYTHON_ROOT'] = str(request.config.rootpath.resolve())

    return new_env
