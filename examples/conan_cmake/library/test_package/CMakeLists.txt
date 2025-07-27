cmake_minimum_required(VERSION 3.24)

project(MathUtilsConsumer LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(mathutils REQUIRED)

add_executable(consumer main.cpp)
target_link_libraries(consumer PRIVATE mathutils::mathutils)
