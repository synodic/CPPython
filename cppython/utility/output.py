"""Session-scoped output management for CPPython.

Provides :class:`OutputSession` (one per CLI invocation / build backend call)
which owns a single temporary log file, and :class:`SpinnerContext` (one per
logical operation) which drives a Rich spinner.

Usage::

    with OutputSession(console, verbose=False) as session:
        with session.spinner('Installing dependencies...'):
            provider.install()
        with session.spinner('Building project...'):
            generator.build()
    # session.__exit__ prints the log file path

When no session is needed (e.g. tests, library usage), use
:data:`NULL_SESSION` which is always available, requires no ``with`` block,
and whose :meth:`spinner` returns a silent no-op context manager.
"""

import contextlib
import logging
import tempfile
from pathlib import Path
from types import TracebackType
from typing import Protocol

from rich.console import Console
from rich.status import Status

# ---------------------------------------------------------------------------
# Spinner
# ---------------------------------------------------------------------------


class SpinnerContext:
    """A context manager that shows a Rich spinner for a single operation.

    When *verbose* is ``True`` the spinner is not shown — phase transitions
    are printed as plain text lines instead.
    """

    def __init__(self, description: str, console: Console, verbose: bool) -> None:
        """Initialize the spinner context.

        Args:
            description: Text shown next to the spinner.
            console: The Rich console used for output.
            verbose: When ``True``, print plain text instead of a spinner.
        """
        self._description = description
        self._console = console
        self._verbose = verbose
        self._status: Status | None = None

    def __enter__(self) -> SpinnerContext:
        """Start the spinner or print the phase header in verbose mode."""
        if self._verbose:
            self._console.print(f'[bold]> {self._description}[/bold]')
        else:
            self._status = self._console.status(self._description, spinner='dots')
            self._status.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Stop the spinner if it is running."""
        if self._status is not None:
            self._status.stop()
            self._status = None

    def update(self, message: str) -> None:
        """Change the spinner / status text."""
        if self._verbose:
            self._console.print(f'  {message}')
        elif self._status is not None:
            self._status.update(message)


# ---------------------------------------------------------------------------
# Session protocol — allows Project to depend on an interface, not a class
# ---------------------------------------------------------------------------


class SessionProtocol(Protocol):
    """Minimal interface that :class:`Project` depends on."""

    def spinner(self, description: str) -> contextlib.AbstractContextManager[SpinnerContext | None]:
        """Return a context manager that optionally shows a spinner."""
        ...


# ---------------------------------------------------------------------------
# Null (no-op) session — used when no output management is desired
# ---------------------------------------------------------------------------


class _NullSession:
    """A session that does nothing.  Always safe to call without a ``with`` block."""

    @contextlib.contextmanager
    def spinner(self, description: str):
        """Yield immediately — no spinner, no output."""
        yield None


NULL_SESSION: SessionProtocol = _NullSession()
"""Singleton no-op session.  Assign to ``Project.session`` when you don't
want spinners or a log file (tests, library usage, etc.)."""


# ---------------------------------------------------------------------------
# Real output session
# ---------------------------------------------------------------------------


class OutputSession:
    """Session-scoped output controller.

    Owns a single temporary log file for the entire invocation.  All
    ``cppython.*`` logger output is routed to this file via a
    :class:`logging.FileHandler`.  In quiet mode (default) the
    ``RichHandler`` on the logger is temporarily removed so nothing is
    printed to the terminal — only the spinner is visible.

    On exit the path to the log file is printed.  If an exception is
    propagating a red error banner is shown as well.
    """

    def __init__(self, console: Console, *, verbose: bool) -> None:
        """Initialize the output session.

        Args:
            console: The Rich console used for spinner and summary output.
            verbose: When ``True``, bypass spinner and print phase headers.
        """
        self._console = console
        self._verbose = verbose
        self._file_handler: logging.FileHandler | None = None
        self._removed_handlers: list[logging.Handler] = []
        self._log_path: Path | None = None
        self._original_level: int | None = None

    # -- context manager ----------------------------------------------------

    def __enter__(self) -> OutputSession:
        """Enter the session: create the log file and configure logging."""
        # Create the session log file
        fd = tempfile.NamedTemporaryFile(  # noqa: SIM115
            mode='w',
            suffix='.log',
            prefix='cppython-',
            delete=False,
        )
        self._log_path = Path(fd.name)
        fd.close()  # We'll let the FileHandler manage the FD

        # Attach a file handler to the root cppython logger
        root_logger = logging.getLogger('cppython')
        self._file_handler = logging.FileHandler(str(self._log_path), mode='w', encoding='utf-8')
        self._file_handler.setLevel(logging.DEBUG)
        self._file_handler.setFormatter(logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s'))
        root_logger.addHandler(self._file_handler)

        # Ensure the root logger level is low enough to let DEBUG through to the file
        if root_logger.level > logging.DEBUG:
            self._original_level = root_logger.level
            root_logger.setLevel(logging.DEBUG)
        else:
            self._original_level = None

        # In quiet mode suppress all console handlers so only the spinner shows
        if not self._verbose:
            for handler in list(root_logger.handlers):
                if handler is not self._file_handler:
                    root_logger.removeHandler(handler)
                    self._removed_handlers.append(handler)

        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Tear down logging, restore handlers, and print the session summary."""
        root_logger = logging.getLogger('cppython')

        # Remove and close the file handler
        if self._file_handler is not None:
            root_logger.removeHandler(self._file_handler)
            self._file_handler.close()
            self._file_handler = None

        # Restore previously removed console handlers
        for handler in self._removed_handlers:
            root_logger.addHandler(handler)
        self._removed_handlers.clear()

        # Restore original log level
        if self._original_level is not None:
            root_logger.setLevel(self._original_level)
            self._original_level = None

        # Print the result
        if exc_type is not None:
            self._console.print(f'[bold red]Error:[/bold red] {exc_val}')
        else:
            self._console.print('[bold green]Done[/bold green]')

        if self._log_path is not None:
            self._console.print(f'Full log: {self._log_path}')

    # -- public API ---------------------------------------------------------

    @property
    def log_path(self) -> Path | None:
        """Path to the session log file, or ``None`` before ``__enter__``."""
        return self._log_path

    def spinner(self, description: str) -> SpinnerContext:
        """Create a spinner context for a logical operation.

        Args:
            description: Text shown next to the spinner.

        Returns:
            A :class:`SpinnerContext` context manager.
        """
        return SpinnerContext(description, self._console, self._verbose)
