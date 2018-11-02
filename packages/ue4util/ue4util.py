import glob, os

class Utility:
    """
    Provides utility functionality for packages consuming conan-ue4cli wrapper packages 
    """
    
    @staticmethod
    def resolve_file(searchdir, name):
        """
        Helper method to resolve the absolute path to a header/library/binary/etc.
        This is useful when the absolute path to a file needs to be passed to Configure/CMake/etc.
        """
        matches = glob.glob(os.path.join(searchdir, "*{}*".format(name)))
        return matches[0] if len(matches) > 0 else None
