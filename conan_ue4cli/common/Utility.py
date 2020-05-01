import glob, importlib.util, os, shutil, subprocess, sys, time
from os.path import basename, dirname, exists, isdir, join

class Utility(object):
	'''
	Provides utility functionality
	'''
	
	@staticmethod
	def repeat(func, maxRetries=5, sleepTime=0.5):
		'''
		Repeatedly calls a function until it succeeds or the max number of retries has been reached
		'''
		for i in range(0, maxRetries):
			try:
				func()
				break
			except:
				time.sleep(sleepTime)
	
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
	def capture(command):
		'''
		Executes the supplied command and captures the output
		'''
		return subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	
	@staticmethod
	def copyFileOrDir(source, destDir):
		'''
		Copies the source file or directory to the destination directory
		'''
		dest = join(destDir, basename(source))
		if isdir(source):
			shutil.copytree(source, dest)
		else:
			shutil.copy2(source, dest)
	
	@staticmethod
	def readFile(filename):
		"""
		Reads data from a file
		"""
		with open(filename, 'rb') as f:
			return f.read().decode('utf-8')
	
	@staticmethod
	def truncateDirectory(dirPath):
		'''
		Ensures the specified directory exists and is empty
		'''
		
		# Delete the directory if it already exists
		# (This can sometimes fail arbitrarily under Windows, so retry a few times if it does)
		if exists(dirPath):
			Utility.repeat(lambda: shutil.rmtree(dirPath))
		
		# Create the directory and any missing parent directories
		os.makedirs(dirPath)
	
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
