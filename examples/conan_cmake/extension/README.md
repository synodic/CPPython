# Example Python Extension with CPPython

A Python extension module built with CPPython's `cppython.build` backend, using Conan-managed C++ dependencies (nanobind, fmt) and scikit-build-core.

## Building

```bash
pip wheel .
```

## Usage

```python
import example_extension

print(example_extension.format_greeting("World"))
# Output: Hello, World! This message was formatted by fmt.
```
