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

    @abstractmethod
    def build(self) -> None:
        """Builds the project"""
        raise NotImplementedError()

    @abstractmethod
    def test(self) -> None:
        """Runs project tests"""
        raise NotImplementedError()

    @abstractmethod
    def bench(self) -> None:
        """Runs project benchmarks"""
        raise NotImplementedError()

    @abstractmethod
    def run(self, target: str) -> None:
        """Runs a built executable

        Args:
            target: The name of the build target to run
        """
        raise NotImplementedError()
