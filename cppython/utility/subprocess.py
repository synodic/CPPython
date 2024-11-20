"""Subprocess definitions"""

import logging
import subprocess
from pathlib import Path
from typing import Any

from cppython.utility.exception import ProcessError


def call(
    arguments: list[str | Path],
    logger: logging.Logger,
    log_level: int = logging.WARNING,
    suppress: bool = False,
    **kwargs: Any,
) -> None:
    """Executes a subprocess call with logger and utility attachments. Captures STDOUT and STDERR

    Args:
        arguments: Arguments to pass to Popen
        logger: The logger to log the process pipes to
        log_level: The level to log to. Defaults to logging.WARNING.
        suppress: Mutes logging output. Defaults to False.
        kwargs: Keyword arguments to pass to subprocess.Popen

    Raises:
        ProcessError: If the underlying process fails
    """
    with subprocess.Popen(arguments, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, **kwargs) as process:
        if process.stdout is None:
            return

        with process.stdout as pipe:
            for line in iter(pipe.readline, ''):
                if not suppress:
                    logger.log(log_level, line.rstrip())

    if process.returncode != 0:
        raise ProcessError('Subprocess task failed')
