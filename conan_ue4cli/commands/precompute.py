import argparse, glob, json, os, subprocess, shutil, sys, tempfile
from os.path import abspath, exists, join
from ..common import ConanTools, LibraryResolver, ProfileManagement, Utility

def precompute(manager, argv):
	
	# Our supported command-line arguments
	parser = argparse.ArgumentParser(
		prog='ue4 conan precompute',
		description = 'Generates precomputed dependency data for UE4 boilerplate modules'
	)
	parser.add_argument('-d', '-dir', dest='dir', metavar='DIR', default=os.getcwd(), help='Specifies the directory containing the boilerplate module for which precomputed data should be created (defaults to the current working directory)')
	parser.add_argument('profile', metavar='profile', choices=ProfileManagement.listGeneratedProfiles(False), help='The Conan profile to precompute dependency data for')
	
	# Parse the supplied command-line arguments
	args = parser.parse_args(argv)
	
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
		
		# Keep track of any additional aggregated flags, including system libraries and macro definitions
		flags = {
			'defines': [],
			'system_libs': []
		}
		
		# Aggregate the data for each of our dependencies
		for dependency in info['dependencies']:
			
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
			
			# Aggregate the static library files from each of the dependency's libraries
			resolver = LibraryResolver(targetPlatform, dependency['lib_paths'])
			for lib in dependency['libs']:
				resolved = resolver.resolve(lib)
				if resolved is not None:
					print('Copying "{}"...'.format(resolved))
					Utility.copyFileOrDir(resolved, libDir)
				else:
					print('Warning: failed to resolve static library file for library name "{}"'.format(lib))
			
			# Add any macro definitions to our list
			flags['defines'] += dependency['defines']
			
			# Add any system libraries to our list
			flags['system_libs'] += dependency['system_libs']
		
		# Write the additional flags to file
		flagsFile = join(args.dir, 'precomputed', engineVersion, targetID, 'flags.json')
		ConanTools.save(flagsFile, json.dumps(flags, sort_keys=True, indent=4))
	
	# Inform the user that aggregation is complete
	print('Done.')
