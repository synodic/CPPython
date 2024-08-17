"""Custom exceptions used by CPPython"""

from pydantic import BaseModel


class ConfigError(BaseModel):
    """Data for ConfigError"""

    message: str


class ConfigException(ValueError):
    """Raised when there is a configuration error"""

    def __init__(self, message: str, errors: list[ConfigError]):

        super().__init__(message)
        self._errors = errors

    @property
    def error_count(self) -> int:
        """The number of configuration errors associated with this exception"""
        return len(self._errors)

    @property
    def errors(self) -> list[ConfigError]:
        """The list of configuration errors"""
        return self._errors


class PluginError(Exception):
    """Raised when there is a plugin error"""

    def __init__(self, error: str) -> None:
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
        self._error = error

        super().__init__(error)

    @property
    def error(self) -> str:
        """Returns the underlying error

        Returns:
            str -- The underlying error
        """
        return self._error
