import argparse, conans, copy, glob, os, platform, re, subprocess, sys, tempfile
from pkg_resources import parse_version
from conans import tools
from os import path

class DelegateManager(object):
	def __init__(self, delegatesDir):
		
		# Read the contents of the default (no-op) delegate class for generated packages
		self.delegatesDir = delegatesDir
		self.defaultDelegate = conans.tools.load(path.join(self.delegatesDir, '__default.py'))
	
	def getDelegateClass(self, libName):
		'''
		Retrieves the delegate class code for the specified package (if one exists),
		or else returns the default (no-op) delegate class
		'''
		delegateFile = path.join(self.delegatesDir, '{}.py'.format(libName))
		if path.exists(delegateFile):
			return conans.tools.load(delegateFile)
		
		return self.defaultDelegate

def _run(command, cwd=None, env=None, check=True):
	'''
	Executes a command and raises an exception if it fails
	'''
	proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd, env=env, universal_newlines=True)
	(stdout, stderr) = proc.communicate(input)
	if proc.returncode != 0 and check == True:
		raise Exception(
			'child process {} failed with exit code {}'.format(command, proc.returncode) +
			'\nstdout: "{}"\nstderr: "{}"'.format(stdout, stderr)
		)
	
	return (stdout, stderr)

def _getClangVersion(clangPath):
	'''
	Retrieves the version number for the specified clang executable
	'''
	(stdout, stderr) = _run([clangPath, '--version'])
	matches = re.search('clang version (.+) \\(', stdout)
	return parse_version(matches.group(1).replace('-', '.'))

def _detectClang(manager):
	'''
	Detects the newest available version of clang and returns a tuple containing (clang, clang++, version)
	'''
	
	# We need to gather the available versions of clang so we can select the newest version
	versions = []
	
	# Check if clang is installed without any suffix
	if conans.tools.which('clang++') != None:
		versions.append(('clang', 'clang++', _getClangVersion('clang++')))
	
	# Check if clang 3.8 or newer is installed with a version suffix
	for ver in reversed(range(38, 60)):
		suffix = '-{:.1f}'.format(ver / 10.0)
		if conans.tools.which('clang++' + suffix) != None:
			versions.append(('clang' + suffix, 'clang++' + suffix, _getClangVersion('clang++' + suffix)))
	
	# Check if UE4 has a bundled version of clang (introduced in UE4.20.0)
	engineRoot = manager.getEngineRoot()
	bundledClang = glob.glob(os.path.join(engineRoot, 'Engine/Extras/ThirdPartyNotUE/SDKs/HostLinux/**/bin/clang'), recursive=True)
	if len(bundledClang) != 0:
		versions.append((bundledClang[0], bundledClang[0] + '++', _getClangVersion(bundledClang[0] + '++')))
	
	# Sort the discovered clang executables in order of version and return the newest one
	versions = sorted(versions, key = lambda v: v[2])
	if len(versions) > 0:
		return versions[-1]
	
	raise Exception('could not detect clang. Please ensure clang 3.8 or newer is installed.')

def _install(packageDir, channel, profile):
	'''
	Installs a package
	'''
	_run(['conan', 'create', '.', 'adamrehn/' + channel, '--profile', profile], cwd=packageDir)

def _generateWrapper(libName, template, delegates, packageDir, channel, profile):
	'''
	Generates and installs a wrapper package
	'''
	conanfile = template.replace('${LIBNAME}', libName)
	conanfile = conanfile.replace('${DELEGATE_CLASS}', delegates.getDelegateClass(libName))
	conans.tools.save(path.join(packageDir, 'conanfile.py'), conanfile)
	_install(packageDir, channel, profile)

def _removeProfile(profile):
	'''
	Removes the UE4 Conan profile if it exists, along with any profile-wide packages
	'''
	print('Removing the "{}" Conan profile if it already exists...'.format(profile))
	profileFile = path.join(conans.paths.get_conan_user_home(), '.conan', 'profiles', profile)
	if path.exists(profileFile):
		os.unlink(profileFile)
	
	print('Removing any previous versions of profile base packages...')
	_run(['conan', 'remove', '--force', '*@adamrehn/profile'])

def generate(manager, argv):
	
	# Our supported command-line arguments
	parser = argparse.ArgumentParser(
		prog='ue4 conan generate',
		description = 'Generates the UE4 Conan profile and associated packages'
	)
	parser.add_argument('--profile-only', action='store_true', help='Create the profile and base packages only, skipping wrapper package generation')
	parser.add_argument('--remove-only', action='store_true', help='Remove any existing profile and base packages only, skipping creation of a new profile')
	
	# Parse the supplied command-line arguments
	args = parser.parse_args(argv)
	
	# Verify that the detected version of UE4 is new enough
	versionFull = manager.getEngineVersion()
	versionMinor = int(manager.getEngineVersion('minor'))
	if versionMinor < 19:
		print('Warning: the detected UE4 version ({}) is too old (4.19.0 or newer required), skipping installation.'.format(versionFull), file=sys.stderr)
		return
	
	# Determine the full path to the directories containing our files
	scriptDir = path.dirname(path.abspath(__file__))
	packagesDir = path.join(scriptDir, 'packages')
	templateDir = path.join(scriptDir, 'template')
	delegatesDir = path.join(scriptDir, 'delegates')
	
	# Read the contents of the template conanfile for generated packages
	template = conans.tools.load(path.join(templateDir, 'conanfile.py'))
	
	# Create the delegate class manager
	delegates = DelegateManager(delegatesDir)
	
	# Create an auto-deleting temporary directory to hold the generated conanfiles
	with tempfile.TemporaryDirectory() as tempDir:
		
		# Use the Conan profile name "ue4" to maintain clean separation from the default Conan profile
		profile = 'ue4'
		
		# Remove the UE4 Conan profile if it exists, along with any profile-wide packages
		_removeProfile(profile)
		
		# If we are only removing the existing Conan profile, stop processing here
		if args.remove_only == True:
			return
		
		# Under Linux, make sure the ue4 Conan profile detects clang instead of GCC
		profileEnv = copy.deepcopy(os.environ)
		if platform.system() == 'Linux':
			clang = _detectClang(manager)
			profileEnv['CC'] = clang[0]
			profileEnv['CXX'] = clang[1]
			print('\nDetected clang version {}:\n{}\n'.format(clang[2], clang[0]))
			print('Detected clang++ version {}:\n{}\n'.format(clang[2], clang[1]))
		
		print('Creating "{}" Conan profile using autodetected settings...'.format(profile))
		_run(['conan', 'profile', 'new', profile, '--detect'], env=profileEnv)
		
		# Under Linux, update the ue4 Conan profile to force the use of clang and libc++
		if platform.system() == 'Linux':
			_run(['conan', 'profile', 'update', 'env.CC={}'.format(profileEnv['CC']), profile])
			_run(['conan', 'profile', 'update', 'env.CXX={}'.format(profileEnv['CXX']), profile])
			_run(['conan', 'profile', 'update', 'settings.compiler.libcxx=libc++', profile])
		
		print('Installing profile base packages...')
		_install(path.join(packagesDir, 'ue4lib'), 'profile', profile)
		_install(path.join(packagesDir, 'libcxx'), 'profile', profile)
		_install(path.join(packagesDir, 'ue4util'), 'profile', profile)
		
		# If we are only creating the Conan profile, stop processing here
		if args.profile_only == True:
			print('Skipping wrapper package generation.')
			return
		
		# Verify that we are not attempting to generate wrapper packages for an Installed Build of the Engine
		if manager.isInstalledBuild() == True:
			print('\n'.join([
				'',
				'Error: attempting to generate wrappers using an Installed Build of UE4!',
				'',
				'Installed Builds do not contain all the files necessary for wrapper generation.',
				'Please use `ue4 setroot` to point ue4cli to the root of the UE4 source tree.',
				'Be sure to have run Setup.{} first to download all third-party dependencies.'.format('bat' if platform.system() == 'Windows' else 'sh'),
				'',
				'Once the wrappers are generated, you can point ue4cli back to the Installed',
				'Build and run `ue4 conan generate --profile-only` to ensure the "{}" Conan'.format(profile),
				'profile reflects the settings for the Installed Build and not the source tree.'
			]), file=sys.stderr)
			sys.exit(1)
		
		# Use the short form of the UE4 version string (e.g 4.19) as the channel for our installed packages
		channel = manager.getEngineVersion('short')
		
		print('Retrieving thirdparty library list from UBT...')
		libs = [lib for lib in manager.listThirdPartyLibs() if lib != 'libc++']
		
		print('Removing any previous versions of generated wrapper packages for {}...'.format(channel))
		_run(['conan', 'remove', '--force', '*/ue4@adamrehn/{}'.format(channel)], check=False)
		
		# Generate the package for each UE4-bundled thirdparty library
		for lib in libs:
			print('Generating and installing wrapper package for {}...'.format(lib))
			_generateWrapper(lib, template, delegates, tempDir, channel, profile)
		print('Done.')
