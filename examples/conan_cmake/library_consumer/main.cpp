#include <mathutils/mathutils.h>
#include <iostream>

int main()
{
    // Test the mathutils library
    std::cout << "Testing MathUtils library..." << std::endl;

    double result1 = mathutils::add(5.0, 3.0);
    double result2 = mathutils::multiply(4.0, 2.5);

    std::cout << "MathUtils tests completed successfully!" << std::endl;
    return 0;
}
