import argparse, glob, json, os, subprocess, shutil, sys, tempfile
from os.path import abspath, exists, join
from ..common import ConanTools, LibraryResolver, ProfileManagement, Utility


# Retrieves the Unreal Engine module name for a third-party library wrapper package
def getUnrealModule(package):
	
	# Verify that the specified package is a wrapper package
	if package['version'] != 'ue4' or package['description'] != 'GENERATED WRAPPER FOR: {}'.format(package['name']):
		return None
	
	# For wrapper packages, the package name is the Unreal Engine module name
	return package['name']


def precompute(manager, argv):
	
	# Our supported command-line arguments
	parser = argparse.ArgumentParser(
		prog='ue4 conan precompute',
		description = 'Generates precomputed dependency data for UE4 boilerplate modules'
	)
	parser.add_argument('-d', '-dir', dest='dir', metavar='DIR', default=os.getcwd(), help='Specifies the directory containing the boilerplate module for which precomputed data should be created (defaults to the current working directory)')
	parser.add_argument('profile', metavar='profile', choices=ProfileManagement.listGeneratedProfiles(False) + ['host'], help='The Conan profile to precompute dependency data for')
	
	# Parse the supplied command-line arguments
	args = parser.parse_args(argv)
	
	# If the user specified "host" as the profile then use the default profile for the host platform
	if args.profile == 'host':
		args.profile = ProfileManagement.profileForHostPlatform(manager)
		print('Using profile for host platform "{}"'.format(args.profile))
	
	# Verify that the specified directory contains a conanfile
	args.dir = abspath(args.dir)
	if not exists(join(args.dir, 'conanfile.py')):
		print('Error: could not find a conanfile.py in the directory "{}"'.format(args.dir))
		sys.exit(1)
	
	# Retrieve the Unreal Engine version string from the specified Conan profile
	engineVersion = ProfileManagement.profileEngineVersion(args.profile)
	
	# Retrieve the Conan target platform from the specified Conan profile
	targetPlatform = ProfileManagement.profilePlatform(args.profile)
	
	# Retrieve the target identifier from the specified Conan profile
	components = args.profile.split('-', 1)
	targetID = components[1]
	
	# Create an auto-deleting temporary directory to hold our Conan build output
	with tempfile.TemporaryDirectory() as tempDir:
		
		# Run `conan install` to install the dependencies for the target profile and generate our JSON dependency info
		subprocess.run(['conan', 'install', args.dir, '--profile=' + args.profile, '-g=json'], cwd=tempDir, check=True)
		
		# Parse the JSON dependency info
		info = json.loads(Utility.readFile(join(tempDir, 'conanbuildinfo.json')))
		
		# Create an include directory for our aggregated headers
		includeDir = join(args.dir, 'precomputed', engineVersion, targetID, 'include')
		Utility.truncateDirectory(includeDir)
		
		# Create a lib directory for our aggregated libraries
		libDir = join(args.dir, 'precomputed', engineVersion, targetID, 'lib')
		Utility.truncateDirectory(libDir)
		
		# Create a bin directory for aggregated DLLs under Windows
		binDir = join(args.dir, 'precomputed', engineVersion, targetID, 'bin')
		Utility.truncateDirectory(binDir)
		
		# Create a data directory for our aggregated data/resource files
		dataDir = join(args.dir, 'precomputed', engineVersion, targetID, 'data')
		Utility.truncateDirectory(dataDir)
		
		# Keep track of any additional aggregated flags, including system libraries and macro definitions
		flags = {
			'defines': [],
			'system_libs': [],
			'unreal_modules': []
		}
		
		# The list of Unreal Engine modules that are safe to link to when using an Installed Build of the Engine
		# TODO: determine these programmatically instead of simply hardcoding a list of known safe modules
		UNREAL_MODULE_WHITELIST = [
			'libcurl',
			'UElibPNG',
			'zlib'
		]
		
		# Aggregate the data for each of our dependencies
		for dependency in info['dependencies']:
			
			# Don't precompute data for the toolchain wrapper under Linux
			if dependency['name'] == 'toolchain-wrapper':
				continue
			
			# If the dependency is an Unreal-bundled library that we can safely use in Installed Builds, link to its module directly
			module = getUnrealModule(dependency)
			if module is not None and module in UNREAL_MODULE_WHITELIST:
				flags['unreal_modules'].append(module)
				continue
			
			# Eliminate any include directories or library directories that fall outside the package's root directory
			pathFilter = lambda paths: list([p for p in paths if p.startswith(dependency['rootpath'])])
			dependency['include_paths'] = pathFilter(dependency['include_paths'])
			dependency['lib_paths'] = pathFilter(dependency['lib_paths'])
			
			# Eliminate any include directories that are nested inside other listed directories
			nestedDirs = []
			for inner in dependency['include_paths']:
				for outer in dependency['include_paths']:
					if inner != outer and inner.startswith(outer):
						nestedDirs.append(inner)
			dependency['include_paths'] = list([p for p in dependency['include_paths'] if p not in nestedDirs])
			
			# Aggregate the headers from each of the dependency's include directories
			for depIncludeDir in dependency['include_paths']:
				for include in glob.glob(join(depIncludeDir, '*')):
					print('Copying "{}"...'.format(include))
					Utility.copyFileOrDir(include, includeDir)
			
			# Aggregate library files from each of the dependency's libraries
			resolver = LibraryResolver(targetPlatform, dependency['lib_paths'])
			for lib in dependency['libs']:
				resolved = resolver.resolve(lib)
				if resolved is not None:
					print('Copying "{}"...'.format(resolved))
					Utility.copyFileOrDir(resolved, libDir)
				else:
					print('Warning: failed to resolve library file for library name "{}"'.format(lib))
			
			# Aggregate DLL files from each of the dependency's binary directories under Windows
			for depBinDir in dependency['bin_paths']:
				for dll in glob.glob(join(depBinDir, '*.dll')):
					print('Copying "{}"...'.format(dll))
					Utility.copyFileOrDir(dll, binDir)
			
			# Aggregate the files from each of the dependency's resource directories
			for depResourceDir in dependency['res_paths']:
				for file in glob.glob(join(depResourceDir, '*')):
					print('Copying "{}"...'.format(file))
					Utility.copyFileOrDir(file, dataDir)
			
			# Add any macro definitions to our list
			flags['defines'] += dependency['defines']
			
			# Add any system libraries to our list
			flags['system_libs'] += dependency['system_libs']
		
		# If any of our generated directories are empty then ensure they won't be ignored by version control
		for directory in [includeDir, libDir, binDir, dataDir]:
			if len(list(os.listdir(directory))) == 0:
				ConanTools.save(join(directory, '.gitignore'), '!.gitignore\n')
		
		# Write the additional flags to file
		flagsFile = join(args.dir, 'precomputed', engineVersion, targetID, 'flags.json')
		ConanTools.save(flagsFile, json.dumps(flags, sort_keys=True, indent=4))
	
	# Inform the user that aggregation is complete
	print('Done.')
