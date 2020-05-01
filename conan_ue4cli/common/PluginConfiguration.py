import os, platform

class PluginConfiguration(object):
	'''
	Provides functionality for managing plugin-wide configuration data
	'''
	
	@staticmethod
	def getConfigDirectory():
		'''
		Determines the platform-specific config directory location for conan-ue4cli
		'''
		if platform.system() == 'Windows':
			return os.path.join(os.environ['APPDATA'], 'conan-ue4cli')
		else:
			return os.path.join(os.environ['HOME'], '.config', 'conan-ue4cli')
