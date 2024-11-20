"""Data definitions for the console application"""

from pydantic import ConfigDict

from cppython.core.schema import CPPythonModel, Interface, ProjectConfiguration


class ConsoleInterface(Interface):
    """Interface implementation to pass to the project"""

    def write_pyproject(self) -> None:
        """Write output"""

    def write_configuration(self) -> None:
        """Write output"""


class ConsoleConfiguration(CPPythonModel):
    """Configuration data for the console application"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    project_configuration: ProjectConfiguration
    interface: Interface
