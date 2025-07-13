"""Exception definitions"""


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


class ProviderInstallationError(Exception):
    """Raised when provider installation fails"""

    def __init__(self, provider_name: str, error: str, original_error: Exception | None = None) -> None:
        """Initializes the error

        Args:
            provider_name: The name of the provider that failed
            error: The error message
            original_error: The original exception that caused this error
        """
        self._provider_name = provider_name
        self._error = error
        self._original_error = original_error

        message = f"Provider '{provider_name}' installation failed: {error}"
        super().__init__(message)

    @property
    def provider_name(self) -> str:
        """Returns the provider name

        Returns:
            str -- The provider name
        """
        return self._provider_name

    @property
    def error(self) -> str:
        """Returns the underlying error

        Returns:
            str -- The underlying error
        """
        return self._error

    @property
    def original_error(self) -> Exception | None:
        """Returns the original exception

        Returns:
            Exception | None -- The original exception if available
        """
        return self._original_error


class ProviderConfigurationError(Exception):
    """Raised when provider configuration is invalid"""

    def __init__(self, provider_name: str, error: str, configuration_key: str | None = None) -> None:
        """Initializes the error

        Args:
            provider_name: The name of the provider with invalid configuration
            error: The error message
            configuration_key: The specific configuration key that caused the error
        """
        self._provider_name = provider_name
        self._error = error
        self._configuration_key = configuration_key

        message = f"Provider '{provider_name}' configuration error"
        if configuration_key:
            message += f" in '{configuration_key}'"
        message += f': {error}'
        super().__init__(message)

    @property
    def provider_name(self) -> str:
        """Returns the provider name

        Returns:
            str -- The provider name
        """
        return self._provider_name

    @property
    def error(self) -> str:
        """Returns the underlying error

        Returns:
            str -- The underlying error
        """
        return self._error

    @property
    def configuration_key(self) -> str | None:
        """Returns the configuration key

        Returns:
            str | None -- The configuration key if available
        """
        return self._configuration_key


class ProviderToolingError(Exception):
    """Raised when provider tooling operations fail"""

    def __init__(self, provider_name: str, operation: str, error: str, original_error: Exception | None = None) -> None:
        """Initializes the error

        Args:
            provider_name: The name of the provider that failed
            operation: The operation that failed (e.g., 'download', 'bootstrap', 'install')
            error: The error message
            original_error: The original exception that caused this error
        """
        self._provider_name = provider_name
        self._operation = operation
        self._error = error
        self._original_error = original_error

        message = f"Provider '{provider_name}' {operation} failed: {error}"
        super().__init__(message)

    @property
    def provider_name(self) -> str:
        """Returns the provider name

        Returns:
            str -- The provider name
        """
        return self._provider_name

    @property
    def operation(self) -> str:
        """Returns the operation that failed

        Returns:
            str -- The operation name
        """
        return self._operation

    @property
    def error(self) -> str:
        """Returns the underlying error

        Returns:
            str -- The underlying error
        """
        return self._error

    @property
    def original_error(self) -> Exception | None:
        """Returns the original exception

        Returns:
            Exception | None -- The original exception if available
        """
        return self._original_error
