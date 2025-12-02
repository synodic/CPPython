# Build Backend

CPPython provides a PEP 517 build backend that wraps [scikit-build-core](https://scikit-build-core.readthedocs.io/), enabling seamless building of Python extension modules with C++ dependencies managed by CPPython.

## Overview

The `cppython.build` backend automatically:

1. Runs the CPPython provider workflow (Conan/vcpkg) to install C++ dependencies
2. Extracts the generated toolchain file
3. Injects `CMAKE_TOOLCHAIN_FILE` into scikit-build-core
4. Delegates the actual wheel building to scikit-build-core

This allows you to define C++ dependencies in `[tool.cppython]` and have them automatically available when building Python extensions.

## Quick Start

Set `cppython.build` as your build backend in `pyproject.toml`:

```toml
[build-system]
requires = ["cppython[conan, cmake]"]
build-backend = "cppython.build"

[project]
name = "my_extension"
version = "1.0.0"

[tool.scikit-build]
cmake.build-type = "Release"

[tool.cppython]
dependencies = ["fmt>=11.0.0", "nanobind>=2.4.0"]

[tool.cppython.generators.cmake]

[tool.cppython.providers.conan]
```

Then build with:

```bash
pip wheel .
```

## Configuration

### Build System Requirements

The `build-system.requires` should include CPPython with the appropriate extras:

```toml
[build-system]
requires = ["cppython[conan, cmake]"]
build-backend = "cppython.build"
```

Available extras:

- `conan` - Conan package manager support
- `cmake` - CMake build system
- `git` - Git SCM support for version detection

### CPPython Configuration

Configure C++ dependencies under `[tool.cppython]`:

```toml
[tool.cppython]
install-path = "install"  # Where provider tools are cached

dependencies = [
    "fmt>=11.0.0",
    "nanobind>=2.4.0",
]

[tool.cppython.generators.cmake]
# CMake generator options

[tool.cppython.providers.conan]
# Conan provider options
```

### scikit-build-core Configuration

All standard `[tool.scikit-build]` options are supported and passed through:

```toml
[tool.scikit-build]
cmake.build-type = "Release"
wheel.packages = ["src/my_package"]
```

CPPython only injects `CMAKE_TOOLCHAIN_FILE` - all other scikit-build-core settings remain under your control.

## How It Works

### Build Workflow

```
pip wheel . / pdm build
        │
        ▼
┌─────────────────────────────────────┐
│         cppython.build              │
├─────────────────────────────────────┤
│ 1. Load pyproject.toml              │
│ 2. Initialize CPPython Project      │
│ 3. Run provider.install()           │
│    └─► Conan/vcpkg installs deps    │
│ 4. Extract toolchain file path      │
│ 5. Inject CMAKE_TOOLCHAIN_FILE      │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│      scikit_build_core.build        │
├─────────────────────────────────────┤
│ 1. Configure CMake with toolchain   │
│ 2. Build extension module           │
│ 3. Package into wheel               │
└─────────────────────────────────────┘
```

### Toolchain Injection

The provider (e.g., Conan) generates a toolchain file containing paths to all installed dependencies. CPPython extracts this path and passes it to scikit-build-core via:

```
cmake.define.CMAKE_TOOLCHAIN_FILE=/path/to/conan_toolchain.cmake
```

This allows CMake's `find_package()` to locate all CPPython-managed dependencies.

## Example Project

A complete example is available at `examples/conan_cmake/extension/`.

### Project Structure

```
my_extension/
├── CMakeLists.txt
├── pyproject.toml
└── src/
    └── my_extension/
        ├── __init__.py
        └── _core.cpp
```

### CMakeLists.txt

```cmake
cmake_minimum_required(VERSION 3.15...3.30)
project(my_extension LANGUAGES CXX)

find_package(Python REQUIRED COMPONENTS Interpreter Development.Module)
find_package(nanobind REQUIRED)
find_package(fmt REQUIRED)

nanobind_add_module(_core src/my_extension/_core.cpp)
target_link_libraries(_core PRIVATE fmt::fmt)
target_compile_features(_core PRIVATE cxx_std_17)

install(TARGETS _core DESTINATION my_extension)
```

### pyproject.toml

```toml
[build-system]
requires = ["cppython[conan, cmake]"]
build-backend = "cppython.build"

[project]
name = "my_extension"
version = "1.0.0"

[tool.scikit-build]
cmake.build-type = "Release"
wheel.packages = ["src/my_extension"]

[tool.cppython]
dependencies = ["fmt>=11.0.0", "nanobind>=2.4.0"]

[tool.cppython.generators.cmake]

[tool.cppython.providers.conan]
```

### C++ Source

```cpp
#include <nanobind/nanobind.h>
#include <fmt/core.h>

namespace nb = nanobind;

std::string greet(const std::string& name) {
    return fmt::format("Hello, {}!", name);
}

NB_MODULE(_core, m) {
    m.def("greet", &greet, nb::arg("name"));
}
```

## Comparison with Alternatives

| Approach | C++ Deps | Python Bindings | Build Backend |
|----------|----------|-----------------|---------------|
| **CPPython + scikit-build-core** | Conan/vcpkg | Any (nanobind, pybind11) | `cppython.build` |
| scikit-build-core alone | Manual/system | Any | `scikit_build_core.build` |
| meson-python | Manual/system | Any | `mesonpy` |

CPPython's advantage is automated C++ dependency management - you declare dependencies in `pyproject.toml` and they're installed automatically during the build.

## Troubleshooting

### Dependencies not found by CMake

Ensure your `CMakeLists.txt` uses `find_package()` for each dependency:

```cmake
find_package(fmt REQUIRED)
target_link_libraries(my_target PRIVATE fmt::fmt)
```

### Build isolation issues

If dependencies aren't being found in isolated builds, ensure `install-path` in `[tool.cppython]` uses an absolute path for caching:

```toml
[tool.cppython]
install-path = "~/.cppython"  # Persists across builds
```

### Viewing build logs

Set scikit-build-core to verbose mode:

```toml
[tool.scikit-build]
logging.level = "DEBUG"
```
