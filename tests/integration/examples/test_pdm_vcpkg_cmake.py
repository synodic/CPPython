"""Example folder tests.

All examples can be run with the CPPython entry-point, and we use the examples as the test data for the CLI.
"""

pytest_plugins = ['tests.fixtures.cmake']


class TestSetup:
    """Verification that the example directory is setup correctly"""
