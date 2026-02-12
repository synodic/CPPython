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
    def build(self, configuration: str | None = None) -> None:
        """Builds the project

        Args:
            configuration: Optional named configuration to use. Interpretation is generator-specific
                (e.g. CMake preset name, Meson build directory).
        """
        raise NotImplementedError()

    @abstractmethod
    def test(self, configuration: str | None = None) -> None:
        """Runs project tests

        Args:
            configuration: Optional named configuration to use. Interpretation is generator-specific.
        """
        raise NotImplementedError()

    @abstractmethod
    def bench(self, configuration: str | None = None) -> None:
        """Runs project benchmarks

        Args:
            configuration: Optional named configuration to use. Interpretation is generator-specific.
        """
        raise NotImplementedError()

    @abstractmethod
    def run(self, target: str, configuration: str | None = None) -> None:
        """Runs a built executable

        Args:
            target: The name of the build target to run
            configuration: Optional named configuration to use. Interpretation is generator-specific.
        """
        raise NotImplementedError()
