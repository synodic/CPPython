"""Project schema specifications"""

from abc import abstractmethod
from typing import Protocol


class API(Protocol):
    """Project API specification"""

    @abstractmethod
    def install(self, groups: list[str] | None = None) -> None:
        """Installs project dependencies

        Args:
            groups: Optional list of dependency groups to install
        """
        raise NotImplementedError()

    @abstractmethod
    def update(self, groups: list[str] | None = None) -> None:
        """Updates project dependencies

        Args:
            groups: Optional list of dependency groups to update
        """
        raise NotImplementedError()
