/**
 * Example Python extension module using nanobind and fmt.
 *
 * This demonstrates how CPPython manages C++ dependencies (fmt, nanobind)
 * via Conan, then scikit-build-core builds the Python extension.
 */

#include <nanobind/nanobind.h>
#include <nanobind/stl/string.h>
#include <fmt/core.h>

namespace nb = nanobind;

/**
 * Format a greeting message using the fmt library.
 *
 * @param name The name to greet
 * @return A formatted greeting string
 */
std::string format_greeting(const std::string &name)
{
    return fmt::format("Hello, {}! This message was formatted by fmt.", name);
}

/**
 * Add two numbers together.
 *
 * @param a First number
 * @param b Second number
 * @return Sum of a and b
 */
int add_numbers(int a, int b)
{
    return a + b;
}

NB_MODULE(_core, m)
{
    m.doc() = "Example extension module built with CPPython + scikit-build-core";

    m.def("format_greeting", &format_greeting, nb::arg("name"),
          "Format a greeting message using the fmt library");

    m.def("add_numbers", &add_numbers, nb::arg("a"), nb::arg("b"),
          "Add two numbers together");
}
