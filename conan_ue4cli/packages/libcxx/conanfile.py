from conans import ConanFile, tools
import os

class LibCxxConan(ConanFile):
    name = "libcxx"
    version = "ue4"
    settings = "os", "compiler", "arch"
    requires = "ue4lib/ue4@adamrehn/profile"
    exports = "*.py"
    
    def package(self):
        self.copy("*")
    
    def package_info(self):
        
        # Provide the libcxx Python module for backwards compatibility with recipes written for older versions of conan-ue4cli
        self.env_info.PYTHONPATH.append(self.package_folder)
