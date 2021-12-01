from os.path import exists, join

class ExecutableResolver(object):
	'''
	Provides functionality for resolving executable files given search paths and library names
	'''
	
	def __init__(self, platform, searchPaths):
		'''
		Creates a new executable resolver for the specified platform and executable search paths
		'''
		self.platform = platform
		self.searchPaths = searchPaths
	
	def resolve(self, executableName):
		'''
		Attempts to resolve the path to the executable file for the specified name
		'''
		
		# Determine the appropriate filename suffix for the target platform
		suffix = '.exe' if self.platform == 'Windows' else ''
		
		# Iterate through each of our search paths and attempt to find the executable file
		for searchDir in self.searchPaths:
			resolved = join(searchDir, executableName + suffix)
			if exists(resolved):
				return resolved
		
		# Failed to resolve the executable file
		return None
