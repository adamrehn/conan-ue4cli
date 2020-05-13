import argparse, os, shutil, tempfile
from os.path import basename, exists, join
from ..common import CommandExecutor, PackageBuilder, ProfileManagement, RecipeCache, RecipeManagement
from .update import update

# The default username used when building packages
DEFAULT_USER = 'adamrehn'

def build(manager, argv):
	
	# Our supported command-line arguments
	parser = argparse.ArgumentParser(
		prog='ue4 conan build',
		description = 'Builds Conan packages using profiles and wrapper packages generated by conan-ue4cli'
	)
	parser.add_argument('--rebuild', action='store_true', help='Rebuild packages that already have binaries in the local Conan cache if their recipes have changed')
	parser.add_argument('--dry-run', action='store_true', help='Print Conan commands instead of running them')
	parser.add_argument('--no-export', action='store_true', help='Do not export package recipes to the local Conan cache')
	parser.add_argument('--no-build', action='store_true', help='Do not build or upload binaries for packages')
	parser.add_argument('--no-cache', action='store_true', help='Do not include recipes from the conan-ue4cli recipe cache when exporting package recipes to the local Conan cache')
	parser.add_argument('--no-cwd', action='store_true', help='Do not include recipes from the current working directory when exporting package recipes to the local Conan cache')
	parser.add_argument('-s', '-source', action='append', dest='sources', metavar='DIR', help='Add the specified directory as an additional source of buildable package recipes (the only sources available by default are the conan-ue4cli recipe cache and the current working directory)')
	parser.add_argument('-o', '-option', action='append', dest='options', metavar='PKG:OPTION=VALUE', help='Specify options to pass to package recipes when building them')
	parser.add_argument('-user', default=DEFAULT_USER, help='Set the user for the built packages (default user is "{}")'.format(DEFAULT_USER))
	parser.add_argument('-upload', default=None, metavar='REMOTE', dest='remote', help='Upload the built packages to the specified Conan remote')
	parser.add_argument('-p', '-profile', dest='profile', metavar='PROFILE', default=None, choices=ProfileManagement.listGeneratedProfiles(), help='Build packages using the specified Conan profile (defaults to the profile for the host platform and the Unreal Engine installation ue4cli is currently acting as an interface for)')
	parser.add_argument('package', nargs='+', help='Package(s) to build, in either NAME or NAME==VERSION format (specify "all" to build all available packages)')
	
	# Parse the supplied command-line arguments
	args = parser.parse_args(argv)
	
	# If a profile was not specified, fallback to the default for the host platform (or use the generic one if the default doesn't exist)
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
	
	# Create a CommandExecutor to run commands or print them, depending on whether we are in dry-run mode
	executor = CommandExecutor(args.dry_run)
	
	# Create our package builder
	builder = PackageBuilder(args.user, channel, args.profile, args.rebuild, executor)
	
	# Keep track of the list of exported package names in case the user asked us to build all available packages
	exported = []
	
	# Determine if we are performing the export step
	if args.no_export == True:
		print('Skipping package recipe export step.')
	else:
		
		# If the recipe cache directory does not exist (usually because this is our first build) and we are including it in our export, then populate it
		cacheDir = RecipeCache.getCacheDirectory()
		if args.no_cache == False and exists(cacheDir) == False:
			update(manager, argv)
		
		# Gather the list of enabled recipe source directories
		sources = []
		if args.no_cache == False:
			sources.append(cacheDir)
		if args.no_cwd == False:
			sources.append(os.getcwd())
		if args.sources is not None:
			sources.extend(args.sources)
		
		# Report the list of recipe source directories to the user
		print('Exporting package recipes from the following source directories:')
		for source in sources:
			print('- {}'.format(source))
		print('', flush=True)
		
		# Iterate over our source directories and export all detected recipes to Conan's local cache
		for source in sources:
			for recipe in RecipeManagement.listRecipesInDir(source):
				
				# Print progress output
				name, version = recipe
				print('Exporting recipe for package "{}/{}@{}/{}"...'.format(name, version, args.user, channel), flush=True)
				
				# Attempt to export the recipe
				builder.export(source, name, version)
				exported.append(name)
		
	# Determine if we are performing the build and upload steps
	if args.no_build == True:
		print('Skipping package build and upload steps.')
		return
	
	# Process the specified list of packages, resolving versions as needed
	packages = []
	for arg in args.package:
		if arg.lower() == 'all':
			if len(exported) == 0:
				raise RuntimeError('the "all" keyword cannot be used when skipping the package recipe export step')
			else:
				packages.extend(list([
					(name, RecipeManagement.getLatestVersion(name, args.user, channel))
					for name in set(exported)
				]))
		elif '==' in arg:
			packages.append(tuple(arg.split('==', 1)))
		else:
			packages.append((arg, RecipeManagement.getLatestVersion(arg, args.user, channel)))
	
	# Report the list of resolved package versions to the user
	uploadSuffix = ' and uploaded to the remote "{}"'.format(args.remote) if args.remote is not None else ''
	print('The following packages will be built{}:'.format(uploadSuffix))
	for package in packages:
		name, version = package
		print('- {}/{}'.format(name, version))
	print('', flush=True)
	
	# Attempt to build each of the packages in turn
	for package in packages:
		
		# Print progress output
		name, version = package
		print('Building package "{}/{}@{}/{}"...'.format(name, version, args.user, channel), flush=True)
		
		# Attempt to build the package
		builder.build(name, version, args.options if args.options is not None else [])
	
	# If a remote has been specified to upload the built packages to, attempt to do so
	if args.remote is not None:
		for package in packages:
			
			# Print progress output
			name, version = package
			print('Uploading package "{}/{}@{}/{}" to remote "{}"...'.format(name, version, args.user, channel, args.remote), flush=True)
			
			# Attempt to upload the package to the specified remote
			builder.upload(name, version, args.remote)
