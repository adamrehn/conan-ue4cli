from .build import build
from .generate import generate
from .update import update
import os, platform, sys

def main(manager, args):
	
	# Our supported subcommands
	SUBCOMMANDS = {
		'build': {
			'function': build,
			'description': 'Builds Conan packages that depend on conan-ue4cli wrappers'
		},
		'generate': {
			'function': generate,
			'description': 'Generates the UE4 Conan profile and associated packages'
		},
		'update': {
			'function': update,
			'description': 'Caches the latest recipe data from the ue4-conan-recipes repo'
		}
	}
	
	# Determine if a subcommand has been specified
	if len(args) > 0:
		
		# Verify that the specified subcommand is valid
		subcommand = args[0]
		if subcommand not in SUBCOMMANDS:
			print('Error: unrecognised subcommand "{}".'.format(subcommand), file=sys.stderr)
			return
		
		# Invoke the subcommand
		SUBCOMMANDS[subcommand]['function'](manager, args[1:])
		
	else:
		
		# Determine the longest subcommand name so we can format our list in nice columns
		longestName = max([len(c) for c in SUBCOMMANDS])
		minSpaces = 6
		
		# Print our list of subcommands
		print('Subcommands:')
		for subcommand in SUBCOMMANDS:
			whitespace = ' ' * ((longestName + minSpaces) - len(subcommand))
			print('  {}{}{}'.format(
				subcommand,
				whitespace,
				SUBCOMMANDS[subcommand]['description']
			))
		print('\nRun `ue4 conan SUBCOMMAND --help` for more information on a subcommand.')
