"""Project schema specifications"""

from abc import abstractmethod
from typing import Protocol


class API(Protocol):
    """Project API specification"""

    @abstractmethod
    def install(self) -> None:
        """Installs project dependencies"""
        raise NotImplementedError()

    @abstractmethod
    def update(self) -> None:
        """Updates project dependencies"""
        raise NotImplementedError()
