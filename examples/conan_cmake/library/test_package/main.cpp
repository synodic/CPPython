import mathutils;
import std;

int main()
{
    std::cout << "Testing MathUtils library..." << std::endl;

    std::cout << "add(5, 3) = " << mathutils::add(5.0, 3.0) << std::endl;
    std::cout << "multiply(4, 2.5) = " << mathutils::multiply(4.0, 2.5) << std::endl;

    std::cout << "MathUtils tests completed successfully!" << std::endl;
    return 0;
}
