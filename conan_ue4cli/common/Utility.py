import glob, importlib.util, os, subprocess, sys
from os.path import basename, dirname, join

class Utility(object):
	'''
	Provides utility functionality
	'''
	
	@staticmethod
	def run(command, cwd=None, env=None, check=True):
		'''
		Executes a command and returns its output, raising an exception if it fails (unless `check` is set to False)
		'''
		proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd, env=env, universal_newlines=True)
		(stdout, stderr) = proc.communicate(input)
		if proc.returncode != 0 and check == True:
			raise Exception(
				'child process {} failed with exit code {}'.format(command, proc.returncode) +
				'\nstdout: "{}"\nstderr: "{}"'.format(stdout, stderr)
			)
		
		return (stdout, stderr)
	
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
