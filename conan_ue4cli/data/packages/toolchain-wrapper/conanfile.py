from conans import ConanFile
import glob, os, tempfile
from os.path import dirname, join

class ToolchainWrapper(ConanFile):
    name = "toolchain-wrapper"
    version = "ue4"
    description = "Wraps a clang compiler toolchain, libc++ and a minimal CentOS 7 sysroot"
    url = "https://github.com/adamrehn/conan-ue4cli/tree/master/conan_ue4cli/packages/toolchain-wrapper"
    homepage = "https://llvm.org/"
    license = "Apache-2.0"
    settings = "os", "compiler", "arch"
    exports = "*.py"
    
    def _find_clang(self, root, architecture):
        '''
        Attempts to locate the clang binary for the specified architecture under the supplied root directory
        '''
        
        # If we've been pointed directly at a clang toolchain then the binary will be directly under the `bin` subdirectory of the root,
        # whereas if we've been pointed at an Unreal Engine toolchain SDK bundle then there will be per-architecture nested subdirectories
        flat = glob.glob(join(root, "bin", "clang"))
        nested = glob.glob(join(root, "*clang*", "*{}*".format(architecture), "bin", "clang"))
        
        # Determine if we can locate clang
        if len(flat) > 0:
            return flat[0]
        elif len(nested) > 0:
            return nested[0]
        else:
            raise RuntimeError('could not locate clang binary for architecture "{}" inside directory "{}"!'.format(architecture, root))
    
    def _find_libcxx(self, root, architecture):
        '''
        Attempts to locate the libc++ static library for the specified architecture under the supplied root directory
        '''
        libraries = glob.glob(join(root, "lib", "Linux", "*{}*".format(architecture), "libc++.a"))
        if len(libraries) > 0:
            return libraries[0]
        else:
            raise RuntimeError('Failed to locate libc++.a for architecture "{}" inside directory "{}"!'.format(architecture, root))
    
    def package(self):
        
        # We currently only support wrapping toolchains targeting Linux
        if self.settings.os != "Linux":
            raise RuntimeError("Only toolchains targeting Linux are supported!")
        
        # We currently only support wrapping toolchains that use clang as the compiler
        if self.settings.compiler != "clang":
            raise RuntimeError("Only toolchains that use clang are supported!")
        
        # Verify that a toolchain path has been supplied for us to wrap
        toolchain = os.environ.get("WRAPPED_TOOLCHAIN", None)
        if toolchain is None:
            raise RuntimeError("Toolchain path must be specified via the WRAPPED_TOOLCHAIN environment variable!")
        
        # Verify that a libc++ path has been supplied for us to wrap
        libcxx = os.environ.get("WRAPPED_LIBCXX", None)
        if libcxx is None:
            raise RuntimeError("libc++ path must be specified via the WRAPPED_LIBCXX environment variable!")
        
        # If we've been pointed to the root SDK directory of an Unreal Engine toolchain, locate the compiler for the target architecture
        architecture = "aarch64" if self.settings.arch == "armv8" else self.settings.arch
        toolchain = dirname(dirname(self._find_clang(toolchain, architecture)))
        
        # Locate the libc++ library files for the target architecture
        libraries = dirname(self._find_libcxx(libcxx, architecture))
        
        # Copy the toolchain files into our package
        print('Copying toolchain files from "{}"...'.format(toolchain))
        self.copy("*", src=toolchain)
        
        # Copy the libc++ header files into our package
        headers = join(libcxx, 'include')
        print('Copying libc++ header files from "{}"...'.format(headers))
        self.copy("*", dst="libc++/include", src=headers)
        
        # Copy the libc++ library files into our package
        print('Copying libc++ library files from "{}"...'.format(libraries))
        self.copy("*", dst="libc++/lib", src=libraries)
        
        # Copy our compiler wrapper scripts into the package
        self.copy("*")
    
    def package_info(self):
        
        # Set the relevant environment variables to ensure downstream build systems use our compiler wrapper scripts
        self.env_info.CC = join(self.package_folder, "wrappers", "clang.py")
        self.env_info.CXX = join(self.package_folder, "wrappers", "clang++.py")
        self.env_info.WRAPPED_CC = join(self.package_folder, "bin", "clang")
        self.env_info.WRAPPED_CXX = join(self.package_folder, "bin", "clang++")
        self.env_info.WRAPPED_LIBCXX = join(self.package_folder, "libc++")
        self.env_info.WRAPPED_SYSROOT = self.package_folder
        self.env_info.LDFLAGS = "---link"
        
        # Ensure our compiler wrapper scripts are executable
        self.run("chmod +x {}/wrappers/clang.py {}/wrappers/clang++.py".format(self.package_folder, self.package_folder))
