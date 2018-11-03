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
        pass
    
    @staticmethod
    def post_info(conanfile):
        '''
        Called at the end of the Conan recipe package_info() method
        '''
        pass
