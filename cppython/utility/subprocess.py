"""Unified subprocess execution for CPPython plugins.

All plugin subprocess calls should go through :func:`run_subprocess` so that
stdout/stderr is captured, logged to the session log file, and hidden from
the terminal unless verbose mode is enabled.
"""

import subprocess
from logging import Logger
from pathlib import Path


def run_subprocess(
    cmd: list[str],
    *,
    cwd: Path | str | None = None,
    logger: Logger,
    **kwargs,
) -> subprocess.CompletedProcess[str]:
    """Run a subprocess with captured output that is routed to the logger.

    Stdout and stderr are always captured (never printed to the terminal
    directly).  Each non-empty line is logged at ``DEBUG`` level so it
    appears in the session log file.  On failure the full output is logged
    at ``ERROR`` level and the :class:`subprocess.CalledProcessError` is
    re-raised.

    Args:
        cmd: The command and arguments to execute.
        cwd: Working directory for the subprocess.
        logger: Logger instance used to record output.
        **kwargs: Additional keyword arguments forwarded to
            :func:`subprocess.run`.  ``capture_output``, ``text``, and
            ``check`` are always overridden.

    Returns:
        The completed process result.

    Raises:
        subprocess.CalledProcessError: If the process exits with a non-zero
            return code.
    """
    # Force capture so output never leaks to the terminal
    kwargs.pop('capture_output', None)
    kwargs.pop('text', None)
    kwargs.pop('check', None)

    logger.debug('Running: %s', ' '.join(cmd))

    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
            **kwargs,
        )
    except subprocess.CalledProcessError as exc:
        # Log everything we have so the session log file is useful
        if exc.stdout:
            for line in exc.stdout.splitlines():
                logger.error('%s', line)
        if exc.stderr:
            for line in exc.stderr.splitlines():
                logger.error('%s', line)
        raise

    # Log successful output at debug level
    if result.stdout:
        for line in result.stdout.splitlines():
            logger.debug('%s', line)
    if result.stderr:
        for line in result.stderr.splitlines():
            logger.debug('%s', line)

    return result
