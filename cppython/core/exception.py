"""Custom exceptions used by CPPython"""

from pydantic import BaseModel


class ConfigError(BaseModel):
    """Data for ConfigError"""

    message: str


class ConfigException(ValueError):
    """Raised when there is a configuration error"""

    def __init__(self, message: str, errors: list[ConfigError]):
        """Initializes the exception"""
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
