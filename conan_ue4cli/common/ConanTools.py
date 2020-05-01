from conans import tools
import inspect


# A dummy config type to pass to Conan
class DummyConfig(object):
	def __getattribute__(self, attr):
		return None


class ConanTools(object):
	'''
	Provides access to Conan utility functionality whilst ensuring all required configuration is performed
	'''
	
	# Keep track of whether we have already configured Conan
	_isConanConfigured = False
	
	@staticmethod
	def get(*args, **kwargs):
		'''
		Wraps `conans.tools.get()`
		'''
		ConanTools._configureConan()
		return tools.get(*args, **kwargs)
	
	@staticmethod
	def load(*args, **kwargs):
		'''
		Wraps `conans.tools.load()`
		'''
		ConanTools._configureConan()
		return tools.load(*args, **kwargs)
	
	@staticmethod
	def save(*args, **kwargs):
		'''
		Wraps `conans.tools.save()`
		'''
		ConanTools._configureConan()
		return tools.save(*args, **kwargs)
	
	@staticmethod
	def _configureConan():
		'''
		Ensures Conan is configured correctly so we can use its utility functionality from outside recipes
		'''
		
		# We only need to perform configuration once
		if ConanTools._isConanConfigured == True:
			return
		
		# Ensure Conan's global configuration object is not `None` when using Conan 1.22.0 or newer
		if hasattr(tools, 'get_global_instances') and hasattr(tools, 'set_global_instances'):
			if 'config' in inspect.signature(tools.set_global_instances).parameters:
				instances = tools.get_global_instances()
				tools.set_global_instances(the_output=instances[0], the_requester=instances[1], config=DummyConfig())
		
		ConanTools._isConanConfigured = True
