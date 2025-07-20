cmake_minimum_required(VERSION 3.24)

project(mathutils VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(fmt REQUIRED)

# Create the library
add_library(mathutils src/mathutils.cpp)

# Set up include directories
target_include_directories(mathutils
    PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)

# Link dependencies
target_link_libraries(mathutils PUBLIC fmt::fmt)