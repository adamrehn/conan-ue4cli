import os

class LibCxx(object):
    
    @staticmethod
    def set_vars(conanFile):
        """
        Applies the necessary overrides to use the UE4-bundled version of libc++ under Linux, using
        the CC and CXX environment variables from the current Conan profile to locate the real clang
        """
        if conanFile.settings.os == "Linux":
            
            # Store the path to the real C compiler
            if "CC" in os.environ:
                os.environ["REAL_CC"] = os.environ["CC"]
            
            # Store the path to the real C++ compiler
            if "CXX" in os.environ:
                os.environ["REAL_CXX"] = os.environ["CXX"]
            
            # Inject our clang wrapper scripts to transparently handle building against libc++
            libcxx = conanFile.deps_env_info["libcxx"]
            os.environ["CC"] = libcxx.CLANG_INTERPOSE_CC
            os.environ["CXX"] = libcxx.CLANG_INTERPOSE_CXX
            os.environ["LDFLAGS"] = libcxx.LDFLAGS
    
    @staticmethod
    def fix_autotools(autotools):
        """
        Fixes the linker flags for the Conan Autotools build helper to work with UE4 libs
        """
        
        # Since Conan's Autotools build helper prefixes all libraries with `-l`,
        # move any absolute library filenames (such as UE4 libs) to the raw linker flags
        isAbsLib = lambda lib: '.' in os.path.basename(lib)
        absLibs = list([lib for lib in autotools.libs if isAbsLib(lib)])
        autotools.libs = list([lib for lib in autotools.libs if isAbsLib(lib) == False])
        autotools.link_flags.extend(absLibs)
