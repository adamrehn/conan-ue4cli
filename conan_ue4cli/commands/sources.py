import argparse, itertools, os, platform, shutil, subprocess, sys, tempfile
from os.path import abspath, exists, isdir, join
from glob import glob
from ..common import ConanTools, PackageManagement, ProfileManagement, RecipeManagement, Utility


# Deletes the specified file or directory
def _delete(path):
	
	# Under Windows, we need to use the `del` command to delete read-only files or directories
	# (And even then it often leaves empty directories behind that need to be cleaned up)
	if platform.system() == 'Windows':
		Utility.run(['del', '/f', '/s', '/q', path], shell=True)
		if isdir(path):
			shutil.rmtree(path, ignore_errors=True)
	else:
		shutil.rmtree(path) if isdir(path) else os.unlink(path)

# Removes any of the specified suffixes from the supplied string
def _stripSuffixes(s, suffixes):
	stripped = s
	for suffix in suffixes:
		stripped = stripped[0: -len(suffix)] if stripped.endswith(suffix) else stripped
	return stripped


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
	conanfiles = itertools.chain.from_iterable([glob(p, recursive=True) if '*' in p else [p] for p in args.conanfile])
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
			
			# Remove any files or directories from the source code that should be excluded (e.g. version control files)
			excludePatterns = ['.git', '.gitattributes', '.gitignore', '.github']
			for match in itertools.chain.from_iterable([glob(join(sourceDir, '**', pattern), recursive=True) for pattern in excludePatterns]):
				print('Excluding: {}'.format(match), flush=True)
				_delete(match)
			
			# Strip any unwanted suffixes from the package name when generating the archive name for the source code
			details = RecipeManagement.parseReference(dependency['reference'])
			name = _stripSuffixes(details['name'], [
				'-ue4'
			])
			
			# If the archive file already exists in our output directory then remove it
			archive = join(args.dir, '{}-{}.zip'.format(name, details['version']))
			if exists(archive):
				print('Removing existing archive: {}'.format(archive), flush=True)
				_delete(archive)
			
			# Compress the source code
			print('Compressing source code for package {}...'.format(dependency['reference']), flush=True)
			shutil.make_archive(_stripSuffixes(archive, ['.zip']), 'zip', sourceDir)
	
	# Inform the user that source code archival is complete
	print('Done.')
