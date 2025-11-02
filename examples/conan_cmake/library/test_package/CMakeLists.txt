cmake_minimum_required(VERSION 4.0)

# Enable std module support for MSVC - MUST be before project()
set(CMAKE_EXPERIMENTAL_CXX_IMPORT_STD "d0edc3af-4c50-42ea-a356-e2862fe7a444")

project(MathUtilsConsumer LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_MODULE_STD ON)

find_package(mathutils REQUIRED)

add_executable(consumer main.cpp)
target_link_libraries(consumer PRIVATE mathutils::mathutils)
