import os
from os.path import exists, join

class LibraryResolver(object):
	'''
	Provides functionality for resolving library files given search paths and library names
	'''
	
	def __init__(self, platform, searchPaths):
		'''
		Creates a new library resolver for the specified platform and library search paths
		'''
		self.platform = platform
		self.searchPaths = searchPaths
	
	def resolve(self, libName):
		'''
		Attempts to resolve the path to the library file for the specified library name
		'''
		
		# Determine the appropriate filename prefix and suffixes for the target platform
		prefix = '' if self.platform == 'Windows' else 'lib'
		suffixes = ['.lib'] if self.platform == 'Windows' else ['.a', '.dylib', '.so']
		
		# Iterate through each of our search paths and attempt to find the library file
		for searchDir in self.searchPaths:
			for suffix in suffixes:
				resolved = join(searchDir, prefix + libName + suffix)
				if exists(resolved):
					return resolved
		
		# Failed to resolve the library file
		return None
