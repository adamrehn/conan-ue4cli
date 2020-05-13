from os.path import basename, dirname, join
from pkg_resources import parse_version
from .Utility import Utility
import glob, re

class RecipeManagement(object):
	'''
	Provides functionality for managing Conan recipes
	'''
	
	@staticmethod
	def getLatestVersion(name, user, channel):
		'''
		Determines the latest available version of the specified Conan package
		'''
		
		# Retrieve the list of available versions of the specified package that are in Conan's local cache
		found = Utility.getJSON(['conan', 'search', '{}/*@{}/{}'.format(name, user, channel)], ['--json', '{}'])
		recipes = [instance['items'] for instance in found['results'] if instance['remote'] is None]
		
		# Verify that at least one version was found
		if len(recipes) == 0:
			raise RuntimeError('could not find the package "{}" in the local Conan cache!'.format(name))
		
		# Extract the list of version numbers and return the highest available version
		references = [RecipeManagement.parseReference(recipe['recipe']['id']) for recipe in recipes[0]]
		versions = sorted([parse_version(reference['version']) for reference in references])
		return str(versions[-1])
	
	@staticmethod
	def listRecipesInDir(directory):
		'''
		Retrieves the list of available package recipes contained in a directory.
		Return value is a list of tuples containing (package, version).
		'''
		recipes = glob.glob(join(directory, '*', '*', 'conanfile.py'))
		return list([
			(basename(dirname(dirname(recipe))),basename(dirname(recipe)))
			for recipe in recipes
		])
	
	@staticmethod
	def parseReference(reference):
		'''
		Parses a fully-qualified Conan package reference into its constituent components
		'''
		match = re.match('(.+)/(.+)@(.+)/(.+)', reference)
		return {
			'name': match.group(1),
			'version': match.group(2),
			'user': match.group(3),
			'channel': match.group(4)
		}
