cmake_minimum_required(VERSION 4.0)

project(mathutils
    VERSION 1.0.0
    DESCRIPTION "A modern math utilities library"
    LANGUAGES CXX
)

include(GNUInstallDirs)
include(CMakePackageConfigHelpers)

# Dependencies
find_package(fmt REQUIRED)

add_library(mathutils)
add_library(mathutils::mathutils ALIAS mathutils)

target_sources(mathutils
    PUBLIC
    FILE_SET CXX_MODULES FILES
    src/mathutils.ixx
)

target_compile_features(mathutils PUBLIC cxx_std_23)
target_link_libraries(mathutils PUBLIC fmt::fmt)

# Generate package config files
write_basic_package_version_file(
    mathutilsConfigVersion.cmake
    VERSION ${PROJECT_VERSION}
    COMPATIBILITY SameMajorVersion
)

configure_package_config_file(
    cmake/mathutilsConfig.cmake.in
    mathutilsConfig.cmake
    INSTALL_DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/mathutils
)

install(
    TARGETS mathutils
    EXPORT mathutilsTargets
    FILE_SET CXX_MODULES
    DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/mathutils/src
)

# Export and package configuration
install(
    EXPORT mathutilsTargets
    FILE mathutilsTargets.cmake
    NAMESPACE mathutils::
    DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/mathutils
    CXX_MODULES_DIRECTORY cxx-modules
)

install(
    FILES
    ${CMAKE_CURRENT_BINARY_DIR}/mathutilsConfig.cmake
    ${CMAKE_CURRENT_BINARY_DIR}/mathutilsConfigVersion.cmake
    DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/mathutils
)