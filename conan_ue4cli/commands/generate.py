from ..common import ConanTools, DelegateManager, PackageManagement, ProfileManagement, Utility
import argparse, copy, glob, os, platform, re, sys, tempfile
from os.path import abspath, dirname, exists, join
from pkg_resources import parse_version

def _getClangVersion(clangPath):
	'''
	Retrieves the version number for the specified clang executable
	'''
	(stdout, stderr) = Utility.run([clangPath, '--version'])
	matches = re.search('clang version (.+) \\(', stdout)
	return parse_version(matches.group(1).replace('-', '.'))

def _locateClang(manager, architecture='x86_64'):
	'''
	Locates the appropriate clang binary for the supplied Unreal Engine installation and build architecture.
	
	Returns a tuple containing (clang, clang++, tempdir) where tempdir is only used for UE4.19
	'''
	
	# Retrieve the minor version number for the supplied Unreal Engine installation
	versionMinor = int(manager.getEngineVersion('minor'))
	
	# Check if the Unreal Engine installation has a bundled version of clang (introduced in UE4.20.0)
	engineRoot = manager.getEngineRoot()
	bundledClang = glob.glob(join(engineRoot, 'Engine/Extras/ThirdPartyNotUE/SDKs/HostLinux/Linux_x64/*clang*/*{}*/bin/clang'.format(architecture)))
	if len(bundledClang) != 0:
		return (bundledClang[0], bundledClang[0] + '++', None)
	elif versionMinor == 19:
		
		# For Unreal Engine 4.19, download the bundled toolchain from 4.20 and use that
		print("Downloading toolchain bundle since Unreal Engine 4.19 doesn't include one...")
		extracted = tempfile.TemporaryDirectory()
		ConanTools.get('https://cdn.unrealengine.com/Toolchain_Linux/native-linux-v11_clang-5.0.0-centos7.tar.gz', destination=extracted.name)
		extractedClang = glob.glob(join(extracted.name, '*clang*/*{}*/bin/clang'.format(architecture)))
		if len(extractedClang) != 0:
			return (extractedClang[0], extractedClang[0] + '++', extracted)
	
	# If we reached this point then we could not locate the appropriate clang binary
	raise Exception('could not locate clang. Please ensure you have run Setup.sh to install the bundled toolchain.')

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
	dataDir = join(dirname(dirname(abspath(__file__))), 'data')
	packagesDir = join(dataDir, 'packages')
	templateDir = join(dataDir, 'wrapper_template')
	delegatesDir = join(dataDir, 'delegates')
	
	# Read the contents of the template conanfile for generated packages
	template = ConanTools.load(join(templateDir, 'conanfile.py'))
	
	# Create the delegate class manager
	delegates = DelegateManager(delegatesDir)
	
	# Create an auto-deleting temporary directory to hold the generated conanfiles
	with tempfile.TemporaryDirectory() as tempDir:
		
		# Generate a profile with an appropriate target suffix for the current Engine version and host platform
		# (This naming scheme will become more useful in future when we support cross-compilation rather than always targeting the host platform)
		profile = ProfileManagement.profileForHostPlatform(manager)
		
		# Remove the UE4 Conan profile if it exists, along with any profile-wide packages
		print('Removing the "{}" Conan profile if it already exists...'.format(profile))
		ProfileManagement.removeProfile(profile)
		print('Removing any previous versions of profile base packages...')
		PackageManagement.removeBasePackages()
		
		# If we are only removing the existing Conan profile, stop processing here
		if args.remove_only == True:
			return
		
		# Under Linux, locate clang and ensure the Conan profile uses it for autodetection
		clang, clangxx, _ = (None, None, None)
		profileEnv = copy.deepcopy(os.environ)
		if platform.system() == 'Linux':
			clang, clangxx, _ = _locateClang(manager)
			profileEnv['CC'] = clang
			profileEnv['CXX'] = clangxx
		
		# Create the ue4 Conan profile
		print('Creating "{}" Conan profile using autodetected settings...'.format(profile))
		Utility.run(['conan', 'profile', 'new', profile, '--detect'], env=profileEnv)
		
		# Use the short form of the UE4 version string (e.g 4.19) as the channel for our installed packages
		channel = manager.getEngineVersion('short')
		
		# Embed the Unreal Engine version string in the ue4 Conan profile so it can be retrieved later if needed
		Utility.run(['conan', 'profile', 'update', 'env.UNREAL_ENGINE_VERSION={}'.format(channel), profile])
		
		print('Installing profile base packages...')
		PackageManagement.install(join(packagesDir, 'ue4lib'), 'profile', profile)
		PackageManagement.install(join(packagesDir, 'libcxx'), 'profile', profile)
		PackageManagement.install(join(packagesDir, 'ue4util'), 'profile', profile)
		
		# Apply our Linux-specific profile modifications
		if platform.system() == 'Linux':
			
			# Update the ue4 Conan profile to ensure libc++ is specified as the C++ standard library
			Utility.run(['conan', 'profile', 'update', 'settings.compiler.libcxx=libc++', profile])
			
			# Update the ue4 Conan profile to add the toolchain wrapper package as a build requirement for all packages
			profilePath = ProfileManagement.conanProfileFile(profile)
			profileConfig = ConanTools.load(profilePath)
			profileConfig = profileConfig.replace('[build_requires]', '[build_requires]\n*: toolchain-wrapper/ue4@adamrehn/{}'.format(channel))
			ConanTools.save(profilePath, profileConfig)
		
		# Duplicate the profile for the host system with the generic name "ue4" to maintain backwards compatibility with legacy versions of conan-ue4cli
		ProfileManagement.duplicateProfile(profile, ProfileManagement.genericProfile())
		
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
		
		print('Retrieving thirdparty library list from UBT...')
		libs = [lib for lib in manager.listThirdPartyLibs() if lib != 'libc++']
		
		print('Removing any previous versions of generated wrapper packages for {}...'.format(channel))
		Utility.run(['conan', 'remove', '--force', '*/ue4@adamrehn/{}'.format(channel)], check=False)
		
		# Under Linux, generate the wrapper package for the bundled clang toolchain and bundled libc++
		if platform.system() == 'Linux':
			
			# Locate the UE4-bundled libc++
			details = manager.getThirdpartyLibs([], includePlatformDefaults = True)
			libcxx = [lib for lib in details.resolveRoot(details.libs, manager.getEngineRoot()) if lib.endswith('libc++.a')][0]
			
			# Wrap the bundled clang toolchain and bundled libc++
			print('Generating and installing toolchain wrapper package...')
			print('  Wrapping clang: {}'.format(clang))
			print('  Wrapping lib++: {}'.format(libcxx))
			PackageManagement.install(join(packagesDir, 'toolchain-wrapper'), channel, profile, [
				'--env', 'WRAPPED_TOOLCHAIN={}'.format(dirname(dirname(clang))),
				'--env', 'WRAPPED_LIBCXX={}'.format(dirname(dirname(dirname(dirname(libcxx)))))
			])
		
		# Generate the package for each UE4-bundled thirdparty library
		for lib in libs:
			print('Generating and installing wrapper package for {}...'.format(lib))
			PackageManagement.generateWrapper(lib, template, delegates, tempDir, channel, profile)
		print('Done.')
