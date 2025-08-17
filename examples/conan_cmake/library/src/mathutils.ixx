export module mathutils;

import fmt;

export namespace mathutils
{
    /**
     * Add two numbers and return the result with formatted output
     * @param a First number
     * @param b Second number
     * @return Sum of a and b
     */
    double add(double a, double b);

    /**
     * Multiply two numbers and return the result with formatted output
     * @param a First number
     * @param b Second number
     * @return Product of a and b
     */
    double multiply(double a, double b);

    /**
     * Print a formatted calculation result
     * @param operation The operation performed
     * @param a First operand
     * @param b Second operand
     * @param result The result of the operation
     */
    void print_result(const char *operation, double a, double b, double result);
}

// Implementation
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
