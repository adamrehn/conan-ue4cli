import argparse, os, shutil, tempfile
from os.path import basename, exists, join
from ..common import PackageBuilder, ProfileManagement, RecipeCache, Utility
from .update import update

# The default username used when building packages
DEFAULT_USER = 'adamrehn'

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
	parser.add_argument('-o', '-option', action='append', dest='options', metavar='PKG:OPTION=VALUE', help='Specify options to pass to package recipes when building them (does not affect dependency resolution)')
	parser.add_argument('-user', default=DEFAULT_USER, help='Set the user for the built packages (default user is "{}")'.format(DEFAULT_USER))
	parser.add_argument('-upload', default=None, metavar='REMOTE', help='Upload the built packages to the specified Conan remote')
	parser.add_argument('-p', '-profile', dest='profile', metavar='PROFILE', default=None, choices=ProfileManagement.listGeneratedProfiles(), help='Build packages using the specified Conan profile (defaults to the profile for the host platform and most Unreal Engine installation used to perform profile generation)')
	parser.add_argument('package', nargs='+', help='Package(s) to build, in either NAME or NAME==VERSION format (specify "all" to build all available packages)')
	
	# Parse the supplied command-line arguments
	args = parser.parse_args(argv)
	
	# If a profile was not specified, fallback to the default for the host platform (or using the generic one if the default doesn't exist)
	if args.profile is None:
		preferredDefault = ProfileManagement.profileForHostPlatform(manager)
		genericFallback = ProfileManagement.genericProfile()
		if preferredDefault in ProfileManagement.listGeneratedProfiles():
			print('Using default profile for host platform "{}"'.format(preferredDefault))
			args.profile = preferredDefault
		else:
			print('Warning: falling back to generic profile "{}" because the profile "{}" does not exist.'.format(genericFallback, preferredDefault))
			print('You should run `ue4 conan generate` to generate the host platform profile for the current Engine installation.')
			args.profile = genericFallback
	
	# Retrieve the Unreal Engine version string for the specified Conan profile and use it as the channel
	channel = ProfileManagement.profileEngineVersion(args.profile)
	
	# Create an auto-deleting temporary directory to hold our aggregated recipe sources
	with tempfile.TemporaryDirectory() as tempDir:
		
		# Determine if we are including the recipe cache directory in our list of source directories
		cacheDir = RecipeCache.getCacheDirectory()
		defaultSources = [os.getcwd()] + ([cacheDir] if args.no_cache == False else [])
		
		# If the recipe cache directory does not exist (usually because this is our first build), then update it
		if args.no_cache == False and exists(cacheDir) == False:
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
		builder = PackageBuilder(tempDir, args.user, channel, args.profile, args.rebuild, args.dry_run)
		
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
		builder.buildPackages(buildOrder, args.options if args.options is not None else [])
		
		# If a remote has been specified to upload the built packages to, attempt to do so
		if args.upload is not None:
			builder.uploadPackages(buildOrder, args.upload)
