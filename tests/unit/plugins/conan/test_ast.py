"""Tests for the AST transformer that modifies ConanFile classes."""

import ast
from textwrap import dedent

import libcst as cst

from cppython.plugins.conan.builder import RequiresTransformer
from cppython.plugins.conan.schema import ConanDependency


class TestTransformer:
    """Unit tests for the RequiresTransformer."""

    class MockDependency(ConanDependency):
        """A dummy dependency class for testing."""

        @staticmethod
        def requires() -> str:
            """Return a dummy requires string."""
            return 'test/1.2.3'

    @staticmethod
    def test_add_requires_when_missing() -> None:
        """Test that the transformer adds requires when missing."""
        dependency = TestTransformer.MockDependency(name='test')

        code = """
        class MyFile(ConanFile):
            name = "test"
            version = "1.0"
        """

        module = cst.parse_module(dedent(code))
        transformer = RequiresTransformer([dependency])
        modified = module.visit(transformer)
        assert 'requires = ["test/1.2.3"]' in modified.code

        # Verify the resulting code is valid Python syntax
        ast.parse(modified.code)

    @staticmethod
    def test_replace_existing_requires() -> None:
        """Test that the transformer replaces existing requires."""
        dependency = TestTransformer.MockDependency(name='test')

        code = """
        class MyFile(ConanFile):
            name = "test"
            requires = ["old/0.1"]
            version = "1.0"
        """

        module = cst.parse_module(dedent(code))
        transformer = RequiresTransformer([dependency])
        modified = module.visit(transformer)
        assert 'requires = ["test/1.2.3"]' in modified.code
        assert 'old/0.1' not in modified.code

        # Verify the resulting code is valid Python syntax
        ast.parse(modified.code)

    @staticmethod
    def test_no_conanfile_class() -> None:
        """Test that the transformer does not modify non-ConanFile classes."""
        dependency = TestTransformer.MockDependency(name='test')

        code = """
        class NotConan:
            pass
        """

        module = cst.parse_module(dedent(code))
        transformer = RequiresTransformer([dependency])
        modified = module.visit(transformer)
        # Should not add requires to non-ConanFile classes
        assert 'requires' not in modified.code

        # Verify the resulting code is valid Python syntax
        ast.parse(modified.code)
