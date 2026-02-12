"""Exception definitions"""


class PluginError(Exception):
    """Raised when there is a plugin error."""

    def __init__(self, error: str) -> None:
        """Initializes the error.

        Args:
            error: The error message
        """
        self.error = error
        super().__init__(error)


class NotSupportedError(Exception):
    """Raised when something is not supported."""

    def __init__(self, error: str) -> None:
        """Initializes the error.

        Args:
            error: The error message
        """
        self.error = error
        super().__init__(error)


class ProviderInstallationError(Exception):
    """Raised when provider installation fails."""

    def __init__(self, provider_name: str, error: str, original_error: Exception | None = None) -> None:
        """Initializes the error.

        Args:
            provider_name: The name of the provider that failed
            error: The error message
            original_error: The original exception that caused this error
        """
        self.provider_name = provider_name
        self.error = error
        self.original_error = original_error
        super().__init__(f"Provider '{provider_name}' installation failed: {error}")


class ProviderConfigurationError(Exception):
    """Raised when provider configuration is invalid."""

    def __init__(self, provider_name: str, error: str, configuration_key: str | None = None) -> None:
        """Initializes the error.

        Args:
            provider_name: The name of the provider with invalid configuration
            error: The error message
            configuration_key: The specific configuration key that caused the error
        """
        self.provider_name = provider_name
        self.error = error
        self.configuration_key = configuration_key

        message = f"Provider '{provider_name}' configuration error"
        if configuration_key:
            message += f" in '{configuration_key}'"
        message += f': {error}'
        super().__init__(message)


class InstallationVerificationError(Exception):
    """Raised when provider artifacts are missing and the user needs to run install first."""

    def __init__(self, provider_name: str, missing_artifacts: list[str]) -> None:
        """Initializes the error.

        Args:
            provider_name: The name of the provider whose artifacts are missing
            missing_artifacts: List of descriptions of what is missing
        """
        self.provider_name = provider_name
        self.missing_artifacts = missing_artifacts

        artifact_list = ', '.join(missing_artifacts)
        super().__init__(
            f"Provider '{provider_name}' artifacts not found: {artifact_list}. "
            f"Run 'cppython install' or 'pdm install' before building."
        )


class ProviderToolingError(Exception):
    """Raised when provider tooling operations fail."""

    def __init__(self, provider_name: str, operation: str, error: str, original_error: Exception | None = None) -> None:
        """Initializes the error.

        Args:
            provider_name: The name of the provider that failed
            operation: The operation that failed (e.g., 'download', 'bootstrap', 'install')
            error: The error message
            original_error: The original exception that caused this error
        """
        self.provider_name = provider_name
        self.operation = operation
        self.error = error
        self.original_error = original_error
        super().__init__(f"Provider '{provider_name}' {operation} failed: {error}")
