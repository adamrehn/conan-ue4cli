import itertools, tempfile
from os.path import join

class PackageBuilder:
	'''
	Provides functionality for building Conan packages
	'''
	
	def __init__(self, user, channel, profile, rebuild, executor):
		self._user = user
		self._channel = channel
		self._profile = profile
		self._rebuild = rebuild
		self._executor = executor
	
	def export(self, baseDir, name, version):
		'''
		Exports a package recipe to Conan's local cache
		'''
		self._executor.execute([
			'conan', 'export',
			join(baseDir, name, version, 'conanfile.py'),
			'{}/{}@{}/{}'.format(name, version, self._user, self._channel)
		])
	
	def build(self, name, version, options=[]):
		'''
		Attempts to build the specified Conan package
		'''
		
		# Create an auto-deleting temporary directory to hold the Conan output files that we discard
		with tempfile.TemporaryDirectory() as tempDir:
			
			# Resolve the fully-qualified reference for the package
			package = '{}/{}@{}/{}'.format(name, version, self._user, self._channel)
			
			# Use the appropriate Conan build policy based on whether the user has request we rebuild outdated packaged
			policy = ['--build=outdated', '--build=cascade'] if self._rebuild == True else ['--build=missing']
			
			# Propagate any user-specified options
			optionArgs = list(itertools.chain.from_iterable([['-o', option] for option in options]))
			
			# Attempt to build the package
			command = ['conan', 'install', package, '--profile=' + self._profile] + policy + optionArgs
			self._executor.execute(command, cwd=tempDir, check=True)
	
	def upload(self, name, version, remote):
		'''
		Attempts to upload the specified Conan package to the specified remote
		'''
		package = '{}/{}@{}/{}'.format(name, version, self._user, self._channel)
		self._executor.execute(['conan', 'upload', package, '--all', '--confirm', '-r', remote], check=True)
