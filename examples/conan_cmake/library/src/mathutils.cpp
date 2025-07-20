#include "mathutils/mathutils.h"
#include <fmt/core.h>
#include <fmt/color.h>

namespace mathutils
{
    double add(double a, double b)
    {
        double result = a + b;
        print_result("addition", a, b, result);
        return result;
    }

    double multiply(double a, double b)
    {
        double result = a * b;
        print_result("multiplication", a, b, result);
        return result;
    }

    void print_result(const char *operation, double a, double b, double result)
    {
        fmt::print(fg(fmt::terminal_color::green),
                   "MathUtils {}: {} + {} = {}\n",
                   operation, a, b, result);
    }
}
