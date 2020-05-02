import os
from os.path import exists, join
from .ConanTools import ConanTools

class DelegateManager(object):
	'''
	Manages delegates, which are used to provide package-specific custom functionality for wrapper packages
	'''
	
	def __init__(self, delegatesDir):
		
		# Read the contents of the default (no-op) delegate class for generated packages
		self.delegatesDir = delegatesDir
		self.defaultDelegate = ConanTools.load(join(self.delegatesDir, '__default.py'))
	
	def getDelegateClass(self, libName):
		'''
		Retrieves the delegate class code for the specified package (if one exists),
		or else returns the default (no-op) delegate class
		'''
		delegateFile = join(self.delegatesDir, '{}.py'.format(libName))
		if exists(delegateFile):
			return ConanTools.load(delegateFile)
		
		return self.defaultDelegate
