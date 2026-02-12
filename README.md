# CPPython

A transparent Python management solution for C++ dependencies and building.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE.md)
[![PyPI version](https://img.shields.io/pypi/v/cppython.svg)](https://pypi.org/project/cppython/)

## Goals

1. **CLI** — Provide imperative commands (`build`, `test`, `bench`, `run`, `install`) for managing C++ projects within a Python ecosystem.
2. **Plugin Architecture** — Support pluggable generators (CMake, Meson) and providers (Conan, vcpkg) so users can mix and match toolchains.
3. **PEP 517 Build Backend** — Act as a transparent build backend that delegates to scikit-build-core or meson-python after ensuring C++ dependencies are in place.
4. **Package Manager Integration** — Integrate with Python package managers so that `<manager> install` seamlessly handles C++ dependency installation alongside Python dependencies.

## Features

## Setup

See [Setup](https://synodic.github.io/cppython/setup) for setup instructions.

## Development

We use [pdm](https://pdm-project.org/en/latest/) as our build system and package manager. Scripts for development tasks are defined in `pyproject.toml` under the `[tool.pdm.scripts]` section.

See [Development](https://synodic.github.io/cppython/development) for additional build, test, and installation instructions.

For contribution guidelines, see [CONTRIBUTING.md](https://github.com/synodic/.github/blob/stable/CONTRIBUTING.md).

## Documentation

## License

This project is licensed under the MIT License — see [LICENSE.md](LICENSE.md) for details.

Copyright © 2026 Synodic Software
