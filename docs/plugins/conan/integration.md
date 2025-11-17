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

If you have an existing `conanfile.py`, follow these steps.

**TODO**
