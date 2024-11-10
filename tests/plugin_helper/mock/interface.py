"""Mock interface definitions"""

from cppython.core.schema import Interface


class MockInterface(Interface):
    """A mock interface class for behavior testing"""

    def write_pyproject(self) -> None:
        """Implementation of Interface function"""

    def write_configuration(self) -> None:
        """Implementation of Interface function"""
