import glob, importlib.util, os, sys
from os.path import basename, dirname, join

class Utility(object):
	'''
	Provides utility functionality
	'''
	
	@staticmethod
	def readFile(filename):
		"""
		Reads data from a file
		"""
		with open(filename, 'rb') as f:
			return f.read().decode('utf-8')
	
	@staticmethod
	def listPackagesInDir(directory):
		'''
		Retrieves the list of available package recipes contained in a directory
		'''
		allPackages = glob.glob(join(directory, '*', '*', 'conanfile.py'))
		uniqueNames = set([basename(dirname(dirname(p))) for p in allPackages])
		return list(uniqueNames)
	
	@staticmethod
	def baseNames(classType):
		'''
		Returns the list of base class names for a class type
		'''
		return list([base.__name__ for base in classType.__bases__])
	
	@staticmethod
	def importFile(moduleName, filePath):
		'''
		Imports a Python module from a file
		'''
		
		# Temporarily add the directory containing the file to our search path,
		# in case the imported module uses relative imports
		moduleDir = dirname(filePath)
		sys.path.append(moduleDir)
		
		# Import the module
		spec = importlib.util.spec_from_file_location(moduleName, filePath)
		module = importlib.util.module_from_spec(spec)
		spec.loader.exec_module(module)
		
		# Restore the search path
		sys.path.remove(moduleDir)
		
		return module
