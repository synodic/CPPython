"""Construction of Conan data"""

from pathlib import Path
from string import Template
from textwrap import dedent

import libcst as cst
from pydantic import DirectoryPath

from cppython.plugins.conan.schema import ConanDependency


class RequiresTransformer(cst.CSTTransformer):
    """Transformer to add or update the `requires` attribute in a ConanFile class."""

    def __init__(self, dependencies: list[ConanDependency]) -> None:
        """Initialize the transformer with a list of dependencies."""
        self.dependencies = dependencies

    def _create_requires_assignment(self) -> cst.Assign:
        """Create a `requires` assignment statement."""
        return cst.Assign(
            targets=[cst.AssignTarget(cst.Name('requires'))],
            value=cst.List([
                cst.Element(cst.SimpleString(f'"{dependency.requires()}"')) for dependency in self.dependencies
            ]),
        )

    def leave_ClassDef(self, original_node: cst.ClassDef, updated_node: cst.ClassDef) -> cst.BaseStatement:
        """Modify the class definition to include or update 'requires'.

        Args:
            original_node: The original class definition.
            updated_node: The updated class definition.

        Returns: The modified class definition.
        """
        if self._is_conanfile_class(original_node):
            updated_node = self._update_requires(updated_node)
        return updated_node

    @staticmethod
    def _is_conanfile_class(class_node: cst.ClassDef) -> bool:
        """Check if the class inherits from ConanFile.

        Args:
            class_node: The class definition to check.

        Returns: True if the class inherits from ConanFile, False otherwise.
        """
        return any((isinstance(base.value, cst.Name) and base.value.value == 'ConanFile') for base in class_node.bases)

    def _update_requires(self, updated_node: cst.ClassDef) -> cst.ClassDef:
        """Update or add a 'requires' assignment in a ConanFile class definition."""
        # Check if 'requires' is already defined
        for body_statement_line in updated_node.body.body:
            if not isinstance(body_statement_line, cst.SimpleStatementLine):
                continue

            assignment_statement = body_statement_line.body[0]
            if not isinstance(assignment_statement, cst.Assign):
                continue

            for target in assignment_statement.targets:
                if not isinstance(target.target, cst.Name) or target.target.value != 'requires':
                    continue

                return self._replace_requires(updated_node, body_statement_line, assignment_statement)

        # Find the last attribute assignment before methods
        last_attribute = None
        for body_statement_line in updated_node.body.body:
            if not isinstance(body_statement_line, cst.SimpleStatementLine):
                break
            assignment_statement = body_statement_line.body[0]
            if not isinstance(assignment_statement, cst.Assign):
                break
            last_attribute = body_statement_line

        # Construct a new statement for the 'requires' attribute
        new_statement = cst.SimpleStatementLine(
            body=[self._create_requires_assignment()],
        )

        # Insert the new statement after the last attribute assignment
        if last_attribute is not None:
            new_body = list(updated_node.body.body)
            index = new_body.index(last_attribute)
            new_body.insert(index + 1, new_statement)
        else:
            new_body = [new_statement] + list(updated_node.body.body)

        return updated_node.with_changes(body=updated_node.body.with_changes(body=new_body))

    def _replace_requires(
        self, updated_node: cst.ClassDef, body_statement_line: cst.SimpleStatementLine, assignment_statement: cst.Assign
    ) -> cst.ClassDef:
        """Replace the existing 'requires' assignment with a new one.

        Args:
            updated_node (cst.ClassDef): The class definition to update.
            body_statement_line (cst.SimpleStatementLine): The body item containing the assignment.
            assignment_statement (cst.Assign): The existing assignment statement.

        Returns:
            cst.ClassDef: The updated class definition.
        """
        new_value = cst.List([
            cst.Element(cst.SimpleString(f'"{dependency.requires()}"')) for dependency in self.dependencies
        ])
        new_assignment = assignment_statement.with_changes(value=new_value)
        return updated_node.with_changes(
            body=updated_node.body.with_changes(
                body=[new_assignment if item is body_statement_line else item for item in updated_node.body.body]
            )
        )


class Builder:
    """Aids in building the information needed for the Conan plugin"""

    def __init__(self) -> None:
        """Initialize the builder"""
        self._filename = 'conanfile.py'

    @staticmethod
    def _create_conanfile(conan_file: Path, dependencies: list[ConanDependency]) -> None:
        """Creates a conanfile.py file with the necessary content."""
        template_string = """
        from conan import ConanFile
        from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout

        class MyProject(ConanFile):
            name = "myproject" 
            version = "1.0"
            settings = "os", "compiler", "build_type", "arch"
            requires = ${dependencies}
            generators = "CMakeDeps"

            def layout(self):
                cmake_layout(self)

            def generate(self):
                tc = CMakeToolchain(self)
                tc.generate()

            def build(self):
                cmake = CMake(self)
                cmake.configure()
                cmake.build()"""

        template = Template(dedent(template_string))

        values = {
            'dependencies': [dependency.requires() for dependency in dependencies],
        }

        result = template.substitute(values)

        with open(conan_file, 'w', encoding='utf-8') as file:
            file.write(result)

    def generate_conanfile(self, directory: DirectoryPath, dependencies: list[ConanDependency]) -> None:
        """Generate a conanfile.py file for the project."""
        conan_file = directory / self._filename

        if conan_file.exists():
            source_code = conan_file.read_text(encoding='utf-8')

            module = cst.parse_module(source_code)
            transformer = RequiresTransformer(dependencies)
            modified = module.visit(transformer)

            conan_file.write_text(modified.code, encoding='utf-8')
        else:
            directory.mkdir(parents=True, exist_ok=True)
            self._create_conanfile(conan_file, dependencies)
