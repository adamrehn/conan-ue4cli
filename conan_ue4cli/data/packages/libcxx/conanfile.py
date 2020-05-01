from conans import ConanFile, tools

class LibCxxConan(ConanFile):
    name = "libcxx"
    version = "ue4"
    exports = "*.py"
    build_policy = "missing"
    
    def package(self):
        self.copy("*.py")
    
    def package_info(self):
        
        # Provide the libcxx Python module for backwards compatibility with recipes written for older versions of conan-ue4cli
        self.env_info.PYTHONPATH.append(self.package_folder)
