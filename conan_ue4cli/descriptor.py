from .main import main

__PLUGIN_DESCRIPTOR__ = {
	'action': main,
	'description': 'Invokes conan-ue4cli functionality. Run `ue4 conan` to see the list of supported subcommands.',
	'args': '[SUBCOMMAND] [ARGS]'
}
