"""Conan plugin schema

This module defines Pydantic models used for integrating the Conan
package manager with the CPPython environment. The classes within
provide structured configuration and data needed by the Conan Provider.
"""

from cppython.core.schema import CPPythonModel


class ConanData(CPPythonModel):
    """Resolved conan data"""


class ConanConfiguration(CPPythonModel):
    """Raw conan data"""
