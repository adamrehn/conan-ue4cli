import argparse, glob, importlib.util, io, inspect, json, os, ue4cli, subprocess, shutil, shlex, sys, tempfile
from os.path import abspath, basename, dirname, exists, join
from conans.client.output import ConanOutput
from .RecipeCache import RecipeCache
from collections import deque
from natsort import natsorted
from .update import update
import networkx as nx

# The default username used when building packages
DEFAULT_USER = 'adamrehn'

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

class PackageBuilder(object):
	'''
	Provides functionality for building a set of Conan packages
	'''
	
	def __init__(self, rootDir, user, channel, profile, rebuild, dryRun):
		self.rootDir = rootDir
		self.user = user
		self.channel = channel
		self.profile = profile
		self.rebuild = rebuild
		self.dryRun = dryRun
		
		# Cache our list of available packages
		self.availablePackages = self.listAvailablePackages()
	
	def execute(self, command):
		'''
		Executes the supplied command (or just prints it if we're in dry run mode)
		'''
		if self.dryRun == True:
			print(' '.join([shlex.quote(arg) for arg in command]), file=sys.stderr)
			return True
		else:
			return subprocess.call(command) == 0
	
	def capture(self, command):
		'''
		Executes the supplied command and captures the output
		'''
		return subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	
	def listAvailablePackages(self):
		'''
		Retrieves the list of available packages (just the names, not the versions)
		'''
		return Utility.listPackagesInDir(self.rootDir)
	
	def identifyNewestVersion(self, name):
		'''
		Determines the newest version of a package and returns the identifier (name/version)
		'''
		
		# Attempt to retrieve the list of available versions for the package
		versions = natsorted([basename(dirname(v)) for v in glob.glob(join(self.rootDir, name, '*', 'conanfile.py'))])
		if len(versions) == 0:
			raise RuntimeError('no available versions for package "{}"'.format(name))
		
		return '{}/{}'.format(name, versions[-1])
	
	def parsePackage(self, package):
		'''
		Parses a package identifier (name/version) and returns the components
		'''
		return package.split('/', maxsplit=1)
	
	def stripQualifiers(self, package):
		'''
		Strips the username and channel from a fully-qualified package identifier
		'''
		return package.split('@', maxsplit=1)[0]
	
	def getConanfile(self, package):
		'''
		Retrieves the absolute path to the conanfile.py for a package, checking that it exists
		'''
		
		# Determine if we have a conanfile.py for the specified package
		name, version = self.parsePackage(package)
		conanfile = join(self.rootDir, name, version, 'conanfile.py')
		if not exists(conanfile):
			raise RuntimeError('no conanfile.py found for package "{}"'.format(package))
		
		return conanfile
	
	def extractDependencies(self, package):
		'''
		Retrieves the list of dependencies for a package
		'''
		
		# Import the conanfile and instantiate the first recipe class it contains
		module = Utility.importFile('conanfile', self.getConanfile(package))
		classes = inspect.getmembers(module, inspect.isclass)
		recipes = list([c[1] for c in classes if 'ConanFile' in Utility.baseNames(c[1])])
		recipe = recipes[0](ConanOutput(io.StringIO()), None, user=self.user, channel=self.channel)
		
		# Extract the list of dependencies
		dependencies = list(recipe.requires)
		if hasattr(recipe, 'requirements'):
			setattr(recipe, 'requires', lambda d: dependencies.append(d))
			recipe.requirements()
		
		# Filter the dependencies to include only those we are building from our directory tree,
		# which will all use the same username and channel as the package that requires them
		dependencies = list([
			self.stripQualifiers(d)
			for d in dependencies
			if d.endswith('@{}/{}'.format(self.user, self.channel)) == True and
			self.parsePackage(d)[0] in self.availablePackages
		])
		return dependencies
	
	def buildDependencyGraph(self, packages):
		'''
		Builds the dependency graph for the specified list of packages
		'''
		
		# Create the DAG that will act as our dependency graph
		graph = nx.DiGraph()
		
		# Iteratively process our list of packages
		toProcess = deque(packages)
		while len(toProcess) > 0:
			
			# Add the current package to the graph
			current = toProcess.popleft()
			graph.add_node(current)
			
			# Retrieve the dependencies for the package and add them to the graph
			deps = self.extractDependencies(current)
			for dep in deps:
				graph.add_node(dep)
				graph.add_edge(dep, current)
				toProcess.append(dep)
		
		return graph
	
	def fullyQualifiedIdentifier(self, package):
		'''
		Generates the fully-qualified identifier for the specified package
		'''
		return '{}@{}/{}'.format(package, self.user, self.channel)
	
	def isPackageInCache(self, package):
		'''
		Determines if the specified package exists in the local Conan cache
		'''
		
		# Create a temporary file path for the JSON output
		jsonFile = tempfile.NamedTemporaryFile(delete=False)
		jsonFile.close()
		
		# Attempt to perform the search and parse the JSON output
		try:
			fullyQualified = self.fullyQualifiedIdentifier(package)
			searchResult = self.capture(['conan', 'search', fullyQualified, '--json', jsonFile.name])
			parsedJSON = json.loads(Utility.readFile(jsonFile.name))
		except:
			parsedJSON = {}
		finally:
			os.unlink(jsonFile.name)
		
		# Determine if the package has at least one binary in the cache
		try:
			return len(parsedJSON['results'][0]['items'][0]['packages']) > 0
		except:
			return False
	
	def buildPackage(self, package):
		'''
		Builds an individual package
		'''
		packageDir = dirname(self.getConanfile(package))
		if self.execute(['conan', 'create', packageDir, '{}/{}'.format(self.user, self.channel), '--profile', self.profile]) == False:
			raise RuntimeError('failed to build package "{}"'.format(package))
	
	def uploadPackage(self, package, remote):
		'''
		Uploads the specified package to the specified remote
		'''
		fullyQualified = self.fullyQualifiedIdentifier(package)
		if self.execute(['conan', 'upload', fullyQualified, '--all', '--confirm', '-r', remote]) == False:
			raise RuntimeError('failed to upload package "{}" to remote "{}"'.format(fullyQualified, remote))
	
	def computeBuildOrder(self, packages):
		'''
		Builds the dependency graph for the specified list of packages and computes the build order
		'''
		
		# Build the dependency graph for the packages
		graph = self.buildDependencyGraph(packages)
		
		# Perform a topological sort to determine the build order
		buildOrder = list(nx.topological_sort(graph))
		
		# Determine which packages need to be built
		if self.rebuild == True:
			return buildOrder
		else:
			return list([p for p in buildOrder if self.isPackageInCache(p) == False])
	
	def buildPackages(self, buildOrder):
		'''
		Builds a list of packages using a pre-computed build order
		'''
		for package in buildOrder:
			print('\nBuilding package "{}"...'.format(package))
			self.buildPackage(package)
	
	def uploadPackages(self, packages, remote):
		'''
		Uploads the specified list of packages to the specified remote
		'''
		for package in packages:
			print('\nUploading package "{}"...'.format(package))
			self.uploadPackage(package, remote)

def build(manager, argv):
	
	# Our supported command-line arguments
	parser = argparse.ArgumentParser(
		prog='ue4 conan build',
		description = 'Builds Conan packages that depend on conan-ue4cli wrappers'
	)
	parser.add_argument('--rebuild', action='store_true', help='Rebuild packages that already exist in the local Conan cache')
	parser.add_argument('--dry-run', action='store_true', help='Print Conan commands instead of running them')
	parser.add_argument('--no-cache', action='store_true', help='Do not add the conan-ue4cli recipe cache to the list of default recipe sources')
	parser.add_argument('-s', '-source', action='append', dest='sources', metavar='DIR', help='Add the specified directory as an additional source of buildable package recipes (the only sources available by default are the conan-ue4cli recipe cache and the current working directory)')
	parser.add_argument('-user', default=DEFAULT_USER, help='Set the user for the built packages (default user is "{}")'.format(DEFAULT_USER))
	parser.add_argument('-upload', default=None, metavar='REMOTE', help='Upload the built packages to the specified Conan remote')
	parser.add_argument('package', nargs='+', help='Package(s) to build, in either NAME or NAME==VERSION format (specify "all" to build all available packages)')
	
	# Parse the supplied command-line arguments
	args = parser.parse_args(argv)
	
	# Use the short form of the UE4 version (4.XX) as the channel
	channel = manager.getEngineVersion('short')
	
	# Create an auto-deleting temporary directory to hold our aggregated recipe sources
	with tempfile.TemporaryDirectory() as tempDir:
		
		# Determine if we are including the recipe cache directory in our list of source directories
		cacheDir = RecipeCache.getCacheDirectory()
		defaultSources = [os.getcwd()] + ([cacheDir] if args.no_cache == False else [])
		
		# If the recipe cache directory does not exist (usually because this is our first build), then update it
		if args.no_cache == False and os.path.exists(cacheDir) == False:
			update(manager, argv)
		
		# Iterate over our source directories and copy our recipes to the temp directory
		sources = defaultSources + (args.sources if args.sources is not None else [])
		for source in sources:
			for recipe in Utility.listPackagesInDir(source):
				try:
					shutil.copytree(join(source, recipe), join(tempDir, recipe))
				except FileExistsError as e:
					conflict = basename(str(e).split(': ')[-1].strip('"\''))
					raise RuntimeError('conflicting source directories detected for recipe {}'.format(conflict)) from None
		
		# Create our package builder
		builder = PackageBuilder(tempDir, args.user, channel, 'ue4', args.rebuild, args.dry_run)
		
		# Process the specified list of packages, resolving versions as needed
		packages = []
		for arg in args.package:
			if arg.lower() == 'all':
				packages.extend(list([builder.identifyNewestVersion(p) for p in builder.availablePackages]))
			elif '==' in arg:
				packages.append(arg.replace('==', '/'))
			else:
				packages.append(builder.identifyNewestVersion(arg))
		
		# Perform dependency resolution and compute the build order for the packages
		buildOrder = builder.computeBuildOrder(packages)
		
		# Verify that we are building at least one package
		if len(buildOrder) == 0:
			print('No packages need to be built. Use the --rebuild flag to rebuild existing packages.')
			return
		
		# Report the computed build order to the user
		uploadSuffix = ' and uploaded to the remote "{}"'.format(args.upload) if args.upload is not None else ''
		print('\nThe following packages will be built{}:'.format(uploadSuffix))
		for package in buildOrder:
			print('\t' + package)
		
		# Attempt to build the packages
		builder.buildPackages(buildOrder)
		
		# If a remote has been specified to upload the built packages to, attempt to do so
		if args.upload is not None:
			builder.uploadPackages(buildOrder, args.upload)
