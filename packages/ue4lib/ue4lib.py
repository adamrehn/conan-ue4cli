from ue4cli import UnrealManagerFactory, PrintingFormat

class UE4Lib():
    
    def __init__(self, libName):
        """
        Queries ue4cli to retrieve the details for the specified library
        """
        self.unreal = UnrealManagerFactory.create()
        self.engineRoot = self.unreal.getEngineRoot()
        self.details = self.unreal.getThirdpartyLibs([libName], includePlatformDefaults = False)
    
    def __repr__(self):
        return repr(self.details)
    
    def includedirs(self):
        """
        Returns the header include directories for this library
        """
        return self.details.resolveRoot(self.details.includeDirs, self.engineRoot)
    
    def libdirs(self):
        """
        Returns the library linker directories for this library
        """
        return self.details.resolveRoot(self.details.linkDirs, self.engineRoot)
    
    def libs(self):
        """
        Returns the list of library files for this library
        """
        return self.details.resolveRoot(self.details.libs, self.engineRoot)
    
    def defines(self):
        """
        Returns the preprocessor definitions for this library
        """
        return self.details.resolveRoot(self.details.definitions, self.engineRoot)
    
    def cxxflags(self):
        """
        Returns the compiler flags for this library
        """
        return self.details.resolveRoot(self.details.cxxFlags, self.engineRoot)
    
    def ldflags(self):
        """
        Returns the linker flags for this library
        """
        return self.details.resolveRoot(self.details.ldFlags, self.engineRoot)
    
    def combined_compiler_flags(self):
        """
        Returns the combined compiler flags (defines + includedirs + cxxflags) for this library as a single string
        """
        return self.details.getCompilerFlags(self.engineRoot, PrintingFormat.singleLine())
    
    def combined_linker_flags(self):
        """
        Returns the combined linker flags (libdirs + libs + ldflags) for this library as a single string
        """
        return self.details.getLinkerFlags(self.engineRoot, PrintingFormat.singleLine())
