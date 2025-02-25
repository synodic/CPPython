"""Helpers for working with the filesystem."""

import os
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def isolated_filesystem() -> Generator[Path]:
    """Change the current working directory to the given path for the duration of the test."""
    old_cwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old_cwd)
