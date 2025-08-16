cmake_minimum_required(VERSION 3.24)

project(FormatOutput LANGUAGES CXX C)

set(CMAKE_CXX_STANDARD 14)

find_package(fmt REQUIRED)

add_executable(main src/main.cpp)
target_link_libraries(main PRIVATE fmt::fmt)