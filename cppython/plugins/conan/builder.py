"""Construction of Conan data"""

from pathlib import Path
from string import Template
from textwrap import dedent

from pydantic import DirectoryPath

from cppython.plugins.conan.schema import ConanDependency


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

        # If the file exists then we need to inject our information into it
        if conan_file.exists():
            raise NotImplementedError(
                'Updating existing conanfile.py is not yet supported. Please remove the file and try again.'
            )

        else:
            directory.mkdir(parents=True, exist_ok=True)
            self._create_conanfile(conan_file, dependencies)
