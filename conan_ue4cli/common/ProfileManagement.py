import conans, os, shutil
from os.path import exists, join
from .Utility import Utility

class ProfileManagement(object):
	'''
	Provides functionality for managing Conan profiles
	'''
	
	@staticmethod
	def conanProfileDir():
		'''
		Returns the path to the Conan profiles directory
		'''
		return join(conans.paths.get_conan_user_home(), '.conan', 'profiles')
	
	@staticmethod
	def conanProfileFile(profile):
		'''
		Resolves the path to the file for the specified Conan profile
		'''
		return join(ProfileManagement.conanProfileDir(), profile)
	
	@staticmethod
	def removeProfile(profile):
		'''
		Removes the specified Conan profile if it exists
		'''
		profileFile = ProfileManagement.conanProfileFile(profile)
		if exists(profileFile):
			os.unlink(profileFile)
	
	@staticmethod
	def duplicateProfile(source, dest):
		'''
		Duplicates an existing Conan profile
		'''
		
		# Remove the destination profile if it already exists
		sourceProfile = ProfileManagement.conanProfileFile(source)
		destProfile = ProfileManagement.conanProfileFile(dest)
		if exists(destProfile):
			os.unlink(destProfile)
		
		# Perform the copy
		print('Copying the "{}" Conan profile into a new profile named "{}"...'.format(source, dest))
		shutil.copy2(sourceProfile, destProfile)
