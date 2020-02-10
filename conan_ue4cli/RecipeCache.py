from .PluginConfiguration import PluginConfiguration
from conans import tools
import inspect, os, shutil

# The URL from which we retrieve the zip file containing the latest recipe data
RECIPE_ZIP_URL = 'https://github.com/adamrehn/ue4-conan-recipes/archive/master.zip'

# The root directory name of the files in the recipe data zip file
ZIP_ROOT_DIR = 'ue4-conan-recipes-master'


# A dummy config type to pass to Conan
class DummyConfig(object):
	def __getattribute__(self, attr):
		return None


class RecipeCache(object):
	'''
	Provides functionality for managing the conan-ue4cli recipe cache
	'''
	
	@staticmethod
	def getCacheDirectory():
		'''
		Returns the path to the recipe cache directory
		'''
		return os.path.join(PluginConfiguration.getConfigDirectory(), 'recipes')
	
	@staticmethod
	def updateCache():
		'''
		Updates the contents of the recipe cache with the latest recipes from our repo
		'''
		
		# Ensure Conan's global configuration object is not `None` when using Conan 1.22.0 or newer
		if hasattr(tools, 'get_global_instances') and hasattr(tools, 'set_global_instances'):
			if 'config' in inspect.signature(tools.set_global_instances).parameters:
				instances = tools.get_global_instances()
				tools.set_global_instances(the_output=instances[0], the_requester=instances[1], config=DummyConfig())
		
		# Remove the cache directory if it already exists
		cacheDir = RecipeCache.getCacheDirectory()
		if os.path.exists(cacheDir):
			shutil.rmtree(cacheDir)
		
		# Download and extract the latest recipes from our GitHub repository
		parentDir = os.path.dirname(cacheDir)
		tools.get(RECIPE_ZIP_URL, destination=parentDir)
		shutil.move(os.path.join(parentDir, ZIP_ROOT_DIR), cacheDir)
