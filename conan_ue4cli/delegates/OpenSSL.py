class PackageDelegate(object):
    
    @staticmethod
    def post_requirements(conanfile):
        '''
        Called at the end of the Conan recipe requirements() method
        '''
        pass
    
    @staticmethod
    def post_build(conanfile):
        '''
        Called at the end of the Conan recipe build() method
        '''
        
        # Isolate our imports from the outer Conan recipe
        from os.path import exists, join
        import shutil
        
        # Under Windows, CMake expects the filenames libeay32.lib and ssleay32.lib,
        # but the UE4-bundled versions don't have the "32" suffix, so we need to
        # duplicate the .lib files to ensure CMake can consume the OpenSSL package
        libDir = join(conanfile.package_folder, "lib")
        if exists(join(libDir, "ssleay.lib")) and not exists(join(libDir, "ssleay32.lib")):
            shutil.copy2(join(libDir, "libeay.lib"), join(libDir, "libeay32.lib"))
            shutil.copy2(join(libDir, "ssleay.lib"), join(libDir, "ssleay32.lib"))
    
    @staticmethod
    def post_info(conanfile):
        '''
        Called at the end of the Conan recipe package_info() method
        '''
        pass
