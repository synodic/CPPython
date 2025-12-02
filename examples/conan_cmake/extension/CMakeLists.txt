cmake_minimum_required(VERSION 4.0)
project(example_extension LANGUAGES CXX)

find_package(Python REQUIRED COMPONENTS Interpreter Development.Module)
find_package(nanobind REQUIRED)

find_package(fmt REQUIRED)

# Create the Python extension module using nanobind
nanobind_add_module(_core src/example_extension/_core.cpp)

# Link against fmt library
target_link_libraries(_core PRIVATE fmt::fmt)

# Set C++ standard (nanobind requires C++17+)
target_compile_features(_core PRIVATE cxx_std_17)

# Install the module
install(TARGETS _core DESTINATION example_extension)
