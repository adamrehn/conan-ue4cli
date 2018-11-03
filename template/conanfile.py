from conans import ConanFile, tools
import json, os

# This will be replaced by a package-specific class with the
# name `PackageDelegate` that provides any package-specific logic
${DELEGATE_CLASS}

class ${LIBNAME}Conan(ConanFile):
    name = "${LIBNAME}"
    version = "ue4"
    settings = "os", "compiler", "build_type", "arch"
    requires = (
        "ue4lib/ue4@adamrehn/profile",
        "libcxx/ue4@adamrehn/profile"
    )
    
    def requirements(self):
        
        # Perform any package-specific requirements logic
        PackageDelegate.post_requirements(self)
    
    def flags_filename(self):
        return os.path.join(self.package_folder, "flags.json")
    
    def package(self):
        
        # Retrieve the details for the wrapped library from ue4cli
        from ue4lib import UE4Lib
        details = UE4Lib("${LIBNAME}")
        
        # Copy the header files (and any stray source files) into our package
        for includedir in details.includedirs():
            
            # Filter out any instances where the module has specified the root of
            # the ThirdParty modules tree as an include directory (yes, seriously.)
            if os.path.basename(includedir) != 'ThirdParty':
                self.copy("*.h", "include", src=includedir)
                self.copy("*.hpp", "include", src=includedir)
                self.copy("*.inc", "include", src=includedir)
                self.copy("*.c", "include", src=includedir)
                self.copy("*.cc", "include", src=includedir)
                self.copy("*.cpp", "include", src=includedir)
        
        # Copy any static library files into our package, ignoring shared libraries
        # and gathering a list of any system libraries that need to be linked against
        systemLibs = []
        for lib in details.libs():
            
            # Determine if this is a system library
            if "." not in lib and "/" not in lib and "\\" not in lib:
                systemLibs.append(lib)
            
            # Determine if this is a static library
            elif lib.endswith(".dll") == False and lib.endswith(".so") == False:
                
                # Verify that the library file exists prior to attempting to copy it
                if os.path.exists(lib) == True and os.path.isfile(lib) == True:
                    self.copy(os.path.basename(lib), "lib", src=os.path.dirname(lib))
        
        # Serialise our defines and compiler flags so they can be retrieved later
        flags = {
            "defines":         details.defines(),
            "cppflags":        details.cxxflags(),
            "sharedlinkflags": details.ldflags(),
            "exelinkflags":    details.ldflags(),
            "systemlibs":      systemLibs
        }
        tools.save(self.flags_filename(), json.dumps(flags))
        
        # Perform any package-specific post-build logic
        PackageDelegate.post_build(self)
    
    def package_info(self):
        
        # Retrieve our serialised defines and compiler flags
        flags = json.loads(tools.load(self.flags_filename()))
        self.cpp_info.defines = flags["defines"]
        self.cpp_info.cppflags = flags["cppflags"]
        self.cpp_info.sharedlinkflags = flags["sharedlinkflags"]
        self.cpp_info.exelinkflags = flags["exelinkflags"]
        
        # Export our static libraries and system libraries
        self.cpp_info.libs = tools.collect_libs(self)
        self.cpp_info.libs.extend(flags['systemlibs'])
        
        # Perform any package-specific post-info logic
        PackageDelegate.post_info(self)
