cmake_minimum_required(VERSION 3.24)

project(BuildRequiresExample LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find the abseil package (provided by CMakeDeps generator)
find_package(absl REQUIRED)

# Create the executable
add_executable(main main.cpp)

# Link against abseil libraries
target_link_libraries(main PRIVATE
    absl::strings
    absl::str_format
    absl::base
)