cmake_minimum_required(VERSION 3.30)

project(mathutils
    VERSION 1.0.0
    DESCRIPTION "A modern math utilities library"
    LANGUAGES CXX
)

include(GNUInstallDirs)
include(CMakePackageConfigHelpers)

# Dependencies
find_package(fmt REQUIRED)

# Library target
add_library(mathutils src/mathutils.cpp)
add_library(mathutils::mathutils ALIAS mathutils)

target_compile_features(mathutils PUBLIC cxx_std_17)
target_include_directories(mathutils PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}>
)
target_link_libraries(mathutils PUBLIC fmt::fmt)

# Installation
install(TARGETS mathutils
    EXPORT mathutilsTargets
    INCLUDES DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}
)

install(DIRECTORY include/
    DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}
    FILES_MATCHING PATTERN "*.h*"
)

install(EXPORT mathutilsTargets
    FILE mathutilsTargets.cmake
    NAMESPACE mathutils::
    DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/mathutils
)

# Package configuration
write_basic_package_version_file(
    mathutilsConfigVersion.cmake
    COMPATIBILITY SameMajorVersion
)

configure_package_config_file(
    cmake/mathutilsConfig.cmake.in
    mathutilsConfig.cmake
    INSTALL_DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/mathutils
)

install(FILES
    ${CMAKE_CURRENT_BINARY_DIR}/mathutilsConfig.cmake
    ${CMAKE_CURRENT_BINARY_DIR}/mathutilsConfigVersion.cmake
    DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/mathutils
)