"""Fixtures for interfacing with the CLI."""

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
