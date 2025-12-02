# Configuration Reference

Complete configuration options for the `cppython.build` backend.

## Build System

```toml
[build-system]
requires = ["cppython[conan, cmake]"]
build-backend = "cppython.build"
```

### Extras

| Extra | Description |
|-------|-------------|
| `conan` | Conan package manager support |
| `cmake` | CMake generator support |
| `git` | Git SCM for dynamic versioning |

## CPPython Options

These options are configured under `[tool.cppython]`.

### install-path

Path where provider tools and cached dependencies are stored.

```toml
[tool.cppython]
install-path = "~/.cppython"  # Default
```

- **Type**: Path
- **Default**: `~/.cppython`
- Relative paths are resolved from the project root
- Use absolute path for build isolation compatibility

### tool-path

Local directory for CPPython-generated files (presets, etc.).

```toml
[tool.cppython]
tool-path = "tool"  # Default
```

- **Type**: Path
- **Default**: `tool`

### build-path

Directory for build artifacts.

```toml
[tool.cppython]
build-path = "build"  # Default
```

- **Type**: Path
- **Default**: `build`

### dependencies

List of C++ dependencies in PEP 508-style format.

```toml
[tool.cppython]
dependencies = [
    "fmt>=11.0.0",
    "boost>=1.84.0",
]
```

- **Type**: List of strings
- Syntax follows provider conventions (Conan uses `name>=version`)

### dependency-groups

Named groups of dependencies for optional features.

```toml
[tool.cppython.dependency-groups]
test = ["gtest>=1.14.0"]
dev = ["benchmark>=1.8.0"]
```

- **Type**: Dictionary of string lists

## Provider Configuration

### Conan

```toml
[tool.cppython.providers.conan]
# Conan-specific options
```

See [Conan Plugin Configuration](../plugins/conan/configuration.md) for details.

## Generator Configuration

### CMake

```toml
[tool.cppython.generators.cmake]
preset_file = "CMakePresets.json"  # Default
configuration_name = "default"      # Default
```

## scikit-build-core Passthrough

All `[tool.scikit-build]` options are passed directly to scikit-build-core:

```toml
[tool.scikit-build]
cmake.build-type = "Release"
cmake.args = ["-DSOME_OPTION=ON"]
wheel.packages = ["src/my_package"]
logging.level = "WARNING"
```

CPPython only adds:

- `cmake.define.CMAKE_TOOLCHAIN_FILE` (from provider)

All other settings are untouched.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `CMAKE_TOOLCHAIN_FILE` | Overrides CPPython's injected toolchain (user takes precedence) |
| `CONAN_HOME` | Conan cache location |

## Example: Full Configuration

```toml
[build-system]
requires = ["cppython[conan, cmake, git]"]
build-backend = "cppython.build"

[project]
name = "my_extension"
version = "1.0.0"
requires-python = ">=3.10"

[tool.scikit-build]
cmake.build-type = "Release"
cmake.args = ["-DBUILD_TESTING=OFF"]
wheel.packages = ["src/my_extension"]
wheel.install-dir = "my_extension"

[tool.cppython]
install-path = "~/.cppython"
tool-path = "tool"
build-path = "build"

dependencies = [
    "fmt>=11.0.0",
    "spdlog>=1.14.0",
]

[tool.cppython.dependency-groups]
test = ["gtest>=1.14.0", "benchmark>=1.8.0"]

[tool.cppython.generators.cmake]
preset_file = "CMakePresets.json"
configuration_name = "default"

[tool.cppython.providers.conan]
```
