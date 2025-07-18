#include <iostream>
#include "absl/strings/str_format.h"
#include "absl/strings/string_view.h"
#include "absl/base/macros.h"

int main()
{
    // Demonstrate abseil string formatting
    absl::string_view greeting = "Hello";
    std::string name = "Abseil";

    // Use absl::StrFormat instead of printf-style formatting
    std::string formatted = absl::StrFormat("%s %s! Version: %s",
                                            greeting, name,
                                            ABSL_PACKAGE_VERSION);

    std::cout << formatted << std::endl;

    // Demonstrate some abseil string operations
    std::string message = absl::StrFormat("This example shows tool_requires with CMake %s",
                                          "working correctly!");
    std::cout << message << std::endl;

    return 0;
}