from conans import ConanFile

class ${LIBNAME}Conan(ConanFile):
    name = "${LIBNAME}"
    version = "ue4"
    settings = "os", "compiler", "build_type", "arch"
    requires = (
        "ue4lib/0.0.1@adamrehn/generated",
        "libcxx/ue4@adamrehn/generated"
    )
    
    def package_info(self):
        from ue4lib import UE4Lib
        details = UE4Lib("${LIBNAME}")
        self.cpp_info.includedirs = details.includedirs()
        self.cpp_info.libdirs = details.libdirs()
        self.cpp_info.libs = details.libs()
        self.cpp_info.defines = details.defines()
        self.cpp_info.cppflags = details.cxxflags()
        self.cpp_info.sharedlinkflags = details.ldflags()
        self.cpp_info.exelinkflags = details.ldflags()
