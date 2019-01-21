from .PluginConfiguration import PluginConfiguration
from conans import tools
import os, shutil

# The URL from which we retrieve the zip file containing the latest recipe data
RECIPE_ZIP_URL = 'https://github.com/adamrehn/ue4-conan-recipes/archive/master.zip'

# The root directory name of the files in the recipe data zip file
ZIP_ROOT_DIR = 'ue4-conan-recipes-master'

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
		
		# Remove the cache directory if it already exists
		cacheDir = RecipeCache.getCacheDirectory()
		if os.path.exists(cacheDir):
			shutil.rmtree(cacheDir)
		
		# Download and extract the latest recipes from our GitHub repository
		parentDir = os.path.dirname(cacheDir)
		tools.get(RECIPE_ZIP_URL, destination=parentDir)
		shutil.move(os.path.join(parentDir, ZIP_ROOT_DIR), cacheDir)
