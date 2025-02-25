"""Helpers for working with the filesystem."""

import os
import tempfile
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def isolated_filesystem() -> Generator[Path]:
    """Change the current working directory to the given path for the duration of the test."""
    old_cwd = os.getcwd()

    try:
        with tempfile.TemporaryDirectory() as temp_directory:
            os.chdir(temp_directory)
            yield Path(temp_directory)
    finally:
        os.chdir(old_cwd)
