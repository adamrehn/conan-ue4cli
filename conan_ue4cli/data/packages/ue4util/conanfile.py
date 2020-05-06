from conans import ConanFile

class UE4UtilConan(ConanFile):
    name = "ue4util"
    version = "ue4"
    homepage = "https://github.com/adamrehn/conan-ue4cli"
    author = "Adam Rehn (adam@adamrehn.com)"
    license = "MIT"
    url = "https://github.com/adamrehn/conan-ue4cli/tree/master/conan_ue4cli/data/packages/ue4util"

    exports = "*.py"
    build_policy = "missing"
    
    def package(self):
        self.copy("*.py")
    
    def package_info(self):
        self.env_info.PYTHONPATH.append(self.package_folder)
