from conans import ConanFile, tools
import os

class LibCxxConan(ConanFile):
    name = "libcxx"
    version = "ue4"
    settings = "os", "compiler", "build_type", "arch"
    requires = "ue4lib/ue4@adamrehn/profile"
    exports = ("*.py", "bin")
    
    def package(self):
        self.copy("*")
    
    def package_info(self):
        from ue4lib import UE4Lib
        if self.settings.os == "Linux":
            
            # UE4 only supports clang under Linux
            if self.settings.compiler != "clang":
                raise Exception("UE4 only supports clang under Linux, attempted to use {}!".format(self.settings.compiler))
            
            # Gather our custom compiler and linker flags for building against UE4 libc++
            libcxx = UE4Lib("libc++")
            compilerFlags = libcxx.combined_compiler_flags()
            linkerFlags = libcxx.combined_linker_flags()
            
            # Inject our custom clang wrapper into the relevant build-related environment variables
            # (This allows the use of UE4 libc++ to be transparent when building consumer packages)
            self.env_info.REAL_CC = os.environ["CC"] if "CC" in os.environ else "cc"
            self.env_info.REAL_CXX = os.environ["CXX"] if "CXX" in os.environ else "c++"
            self.env_info.CLANG_INTERPOSE_CXXFLAGS = compilerFlags
            self.env_info.CLANG_INTERPOSE_LDFLAGS = linkerFlags
            self.env_info.CLANG_INTERPOSE_CC = os.path.join(self.package_folder, "bin/clang.py")
            self.env_info.CLANG_INTERPOSE_CXX = os.path.join(self.package_folder, "bin/clang++.py")
            self.env_info.CC = self.env_info.CLANG_INTERPOSE_CC
            self.env_info.CXX = self.env_info.CLANG_INTERPOSE_CXX
            self.env_info.LDFLAGS = "---link"
            
            # Ensure our wrapper scripts are executable
            self.run("chmod +x {}/bin/clang.py {}/bin/clang++.py".format(self.package_folder, self.package_folder))
            
        # Since a Conan profile can override environment variables from recipes, we provide functionality to restore them
        self.env_info.PYTHONPATH.append(self.package_folder)
