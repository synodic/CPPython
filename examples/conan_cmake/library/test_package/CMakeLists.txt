cmake_minimum_required(VERSION 4.0)

project(MathUtilsConsumer LANGUAGES CXX)

# Enable 'import std;' support (requires __CMAKE::CXX23 from compiler detection)
set(CMAKE_CXX_MODULE_STD ON)

find_package(mathutils REQUIRED)

add_executable(consumer main.cpp)
target_link_libraries(consumer PRIVATE mathutils::mathutils)
