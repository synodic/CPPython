from conan import ConanFile
from conan.tools.cmake import CMakeDeps, CMakeToolchain


class MathUtilsConan(ConanFile):
    name = 'mathutils'
    version = '1.0.0'

    settings = 'os', 'compiler', 'build_type', 'arch'

    def configure(self):
        # Enable fmt module support
        self.options['fmt'].with_modules = True

    def generate(self):
        deps = CMakeDeps(self)
        deps.generate()

        tc = CMakeToolchain(self)
        tc.variables['FMT_MODULE'] = True
        tc.generate()
