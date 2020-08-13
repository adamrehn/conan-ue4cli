import argparse, glob, itertools, os, shutil, subprocess, sys, tempfile
from os.path import abspath, exists, join
from ..common import ConanTools, PackageManagement, ProfileManagement, RecipeManagement, Utility

def sources(manager, argv):
	
	# Our supported command-line arguments
	parser = argparse.ArgumentParser(
		prog='ue4 conan sources',
		description = 'Retrieves the source code of the dependencies for one or more conanfiles'
	)
	parser.add_argument('-d', '-dir', dest='dir', metavar='DIR', default=os.getcwd(), help='Specifies output directory where source archives should be generated (defaults to the current working directory)')
	parser.add_argument('profile', metavar='profile', choices=ProfileManagement.listGeneratedProfiles(False) + ['host'], help='The Conan profile to use when retrieving conanfile dependencies')
	parser.add_argument('conanfile', nargs='+', help='Paths (or glob patterns) specifying one or more conanfiles to process')
	
	# Parse the supplied command-line arguments
	args = parser.parse_args(argv)
	
	# If the user specified "host" as the profile then use the default profile for the host platform
	if args.profile == 'host':
		args.profile = ProfileManagement.profileForHostPlatform(manager)
		print('Using profile for host platform "{}"'.format(args.profile))
	
	# Verify that at least one conanfile was specified and that all specified conanfiles actually exist
	conanfiles = itertools.chain.from_iterable([glob.glob(p, recursive=True) if '*' in p else [p] for p in args.conanfile])
	conanfiles = list([abspath(p) for p in conanfiles])
	for conanfile in conanfiles:
		if not exists(conanfile):
			print('Error: the file "{}" does not exist'.format(conanfile))
			sys.exit(1)
	
	# Aggregate the dependencies from all specified conanfiles
	dependencies = list(itertools.chain.from_iterable([
		PackageManagement.getDependencyGraph(conanfile, args.profile)
		for conanfile in conanfiles
	]))
	
	# Filter out any wrapper packages in the list of dependencies
	dependencies = list([
		dep for dep in dependencies
		if dep['is_ref'] is True and RecipeManagement.parseReference(dep['reference'])['version'] not in ['ue4']
	])
	
	# Retrieve the source code for each dependency in turn
	for dependency in dependencies:
		
		# Create an auto-deleting temporary directory to hold the conanfile and uncompressed source code
		with tempfile.TemporaryDirectory() as tempDir:
			
			# Retrieve the conanfile for the dependency
			recipe, _ = Utility.run(['conan', 'get', '--raw', dependency['reference']], check=True)
			conanfile = join(tempDir, 'conanfile.py')
			ConanTools.save(conanfile, recipe)
			
			# Retrieve the source code for the dependency
			sourceDir = join(tempDir, 'source')
			subprocess.run(['conan', 'source', conanfile, '-sf', sourceDir], check=True)
			
			# Compress the source code and place the archive in our output directory
			details = RecipeManagement.parseReference(dependency['reference'])
			shutil.make_archive(join(args.dir, '{}-{}'.format(details['name'], details['version'])), 'zip', sourceDir)
	
	# Inform the user that source code archival is complete
	print('Done.')
