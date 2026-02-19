# Conanfile Integration

CPPython uses a dual-file approach.

## `conanfile_base.py` - Auto-generated

**Auto-generated** from your `pyproject.toml` dependencies. **Do not edit manually** - regenerated on every install/update/publish.

Contains a `CPPythonBase` class with dependencies from `[tool.cppython.dependencies]` and test dependencies from `[tool.cppython.dependency-groups.test]`.

## `conanfile.py` - User-customizable

**Created once** if it doesn't exist, then **never modified** by CPPython. Inherits from `CPPythonBase`.

You can customize this file for package metadata like name, version, and settings, additional dependencies beyond `pyproject.toml`, build configuration and CMake integration, and package and export logic.

**Key requirement** - Always call `super().requirements()` and `super().build_requirements()` to inherit managed dependencies.

## Workflow

- First run - Both files are generated
- Subsequent runs - Only `conanfile_base.py` is regenerated; `conanfile.py` is preserved
- Adding dependencies - Update `pyproject.toml` and run `cppython install`

## Migrating Existing Projects

If you have an existing `conanfile.py`, back it up and run `cppython install` to generate both files. Then update your conanfile to inherit from `CPPythonBase`.

```python
from conan.tools.cmake import CMake, CMakeConfigDeps, CMakeToolchain, cmake_layout
from conanfile_base import CPPythonBase  # Import the base class


class YourPackage(CPPythonBase):  # Inherit from CPPythonBase instead of ConanFile
    name = "your-package"
    version = "1.0.0"
    settings = "os", "compiler", "build_type", "arch"
    exports = "conanfile_base.py"  # Export the base file

    def requirements(self):
        super().requirements()  # Get CPPython managed dependencies
        # Add your custom requirements here
        # self.requires("custom-lib/1.0.0")

    def build_requirements(self):
        super().build_requirements()  # Get CPPython managed test dependencies
        # Add your custom build requirements here

    # ... rest of your configuration
```
