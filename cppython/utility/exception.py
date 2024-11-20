"""Exception definitions"""


class ProcessError(Exception):
    """Raised when there is a configuration error"""

    def __init__(self, error: str) -> None:
        """Initializes the error

        Args:
            error: The error message
        """
        self._error = error

        super().__init__(error)

    @property
    def error(self) -> str:
        """Returns the underlying error

        Returns:
            str -- The underlying error
        """
        return self._error


class PluginError(Exception):
    """Raised when there is a plugin error"""

    def __init__(self, error: str) -> None:
        """Initializes the error

        Args:
            error: The error message
        """
        self._error = error

        super().__init__(error)

    @property
    def error(self) -> str:
        """Returns the underlying error

        Returns:
            str -- The underlying error
        """
        return self._error


class NotSupportedError(Exception):
    """Raised when something is not supported"""

    def __init__(self, error: str) -> None:
        """Initializes the error

        Args:
            error: The error message
        """
        self._error = error

        super().__init__(error)

    @property
    def error(self) -> str:
        """Returns the underlying error

        Returns:
            str -- The underlying error
        """
        return self._error
