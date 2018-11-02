from conans import ConanFile, tools
import json, os

class ${LIBNAME}Conan(ConanFile):
    name = "${LIBNAME}"
    version = "ue4"
    settings = "os", "compiler", "build_type", "arch"
    requires = (
        "ue4lib/ue4@adamrehn/profile",
        "libcxx/ue4@adamrehn/profile"
    )
    
    def flags_filename(self):
        return os.path.join(self.package_folder, "flags.json")
    
    def package(self):
        
        # Retrieve the details for the wrapped library from ue4cli
        from ue4lib import UE4Lib
        details = UE4Lib("${LIBNAME}")
        
        # Serialise our defines and compiler flags so they can be retrieved later
        flags = {
            "defines":         details.defines(),
            "cppflags":        details.cxxflags(),
            "sharedlinkflags": details.ldflags(),
            "exelinkflags":    details.ldflags()
        }
        tools.save(self.flags_filename(), json.dumps(flags))
        
        # Copy the header files (and any stray source files) into our package
        for includedir in details.includedirs():
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
    
    def package_info(self):
        
        # Export all of our static libraries
        self.cpp_info.libs = tools.collect_libs(self)
        
        # Retrieve our serialised defines and compiler flags
        flags = json.loads(tools.load(self.flags_filename()))
        self.cpp_info.defines = flags["defines"]
        self.cpp_info.cppflags = flags["cppflags"]
        self.cpp_info.sharedlinkflags = flags["sharedlinkflags"]
        self.cpp_info.exelinkflags = flags["exelinkflags"]
