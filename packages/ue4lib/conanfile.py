from conans import ConanFile

class UE4LibConan(ConanFile):
    name = "ue4lib"
    version = "0.0.1"
    exports = "*"
    build_policy = "missing"
    
    def package(self):
        self.copy("*.py")
    
    def package_info(self):
        self.env_info.PYTHONPATH.append(self.package_folder)
