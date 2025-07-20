#pragma once

namespace mathutils
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
