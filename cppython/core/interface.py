"""Default interface implementations."""

from cppython.core.schema import Interface


class NoOpInterface(Interface):
    """No-op implementation of Interface.

    Used when no write-back to configuration files is needed,
    e.g. in the build backend and console application contexts.
    """

    def write_pyproject(self) -> None:
        """No-op."""

    def write_configuration(self) -> None:
        """No-op."""

    def write_user_configuration(self) -> None:
        """No-op."""
