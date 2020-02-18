import os

class LibCxx(object):
    
    @staticmethod
    def set_vars(conanFile):
        """
        This is a no-op provided for backwards compatibility with recipes written for older versions of conan-ue4cli
        """
        LibCxx._show_deprecation_notice()
    
    @staticmethod
    def fix_autotools(autotools):
        """
        This is a no-op provided for backwards compatibility with recipes written for older versions of conan-ue4cli
        """
        LibCxx._show_deprecation_notice()
    
    @staticmethod
    def _show_deprecation_notice():
        print("Warning: the libcxx package has been deprecated and will be removed in a future version of conan-ue4cli.")
