import subprocess, sys

class CommandExecutor(object):
	'''
	Provides functionality for executing commands (or simply printing them when in dry run mode)
	'''
	
	def __init__(self, dryRun=False):
		self._dryRun = dryRun
	
	def execute(self, command, **kwargs):
		'''
		Executes the supplied command (or just prints it if we're in dry run mode)
		'''
		print(command, file=sys.stderr, flush=True)
		if self._dryRun == True:
			return True
		else:
			return subprocess.run(command, **kwargs).returncode == 0
