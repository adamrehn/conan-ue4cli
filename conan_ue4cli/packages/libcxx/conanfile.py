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
            
            # Store the path to our custom clang wrapper in the relevant build-related environment variables.
            # The UE4 Conan profile will override CC and CXX with the correct clang for the UE4 installation being used, and
            # LibCxx.set_vars() will then populate REAL_CC and REAL_CXX with the correct paths when UE4-compatible packages are built.
            # (This allows the use of UE4 libc++ to be transparent to build systems such as CMake and GNU Autotools.)
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
        
        # Since the UE4 Conan profile will provide the path to clang for the current Engine installation,
        # UE4-compatible packages will need to call LibCxx.set_vars() to enable our compiler interposition
        self.env_info.PYTHONPATH.append(self.package_folder)
