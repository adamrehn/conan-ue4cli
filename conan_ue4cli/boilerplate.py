import argparse, os, re, sys
from .ConanTools import ConanTools
from .version import __version__
from os.path import abspath, dirname, join

def boilerplate(manager, argv):
	
	# Our supported command-line arguments
	parser = argparse.ArgumentParser(
		prog='ue4 conan boilerplate',
		description = 'Generates UE4 modules with boilerplate code for wrapping external dependencies'
	)
	parser.add_argument('name', help='The name of the module that will be generated')
	parser.add_argument('-outdir', default=os.getcwd(), help='Specify the output directory where the generated module will be placed (default is the current working directory)')
	
	# Parse the supplied command-line arguments
	args = parser.parse_args(argv)
	
	# Verify that the detected version of UE4 is new enough
	versionFull = manager.getEngineVersion()
	versionMinor = int(manager.getEngineVersion('minor'))
	if versionMinor < 19:
		print('Error: the detected UE4 version ({}) is too old. 4.19.0 or newer is required.'.format(versionFull), file=sys.stderr)
		sys.exit(1)
	
	# Select the appropriate template version for the detected version of UE4
	if versionMinor == 19:
		templateVersion = 1
	elif versionMinor >= 20 and versionMinor <= 23:
		templateVersion = 2
	else:
		templateVersion = 3
	
	# Determine the full path to the directory containing our templates
	scriptDir = dirname(abspath(__file__))
	templateDir = join(scriptDir, 'boilerplate_templates')
	
	# Read the contents of the template .Build.cs file
	template = ConanTools.load(join(templateDir, 'v{}'.format(templateVersion), 'Template.Build.cs'))
	
	# Sanitise the module name to ensure it represents a valid C# identifier
	validStart = re.compile('[_|\D]')
	moduleName = re.sub('\W', '', args.name)
	while validStart.match(moduleName, 0, 1) is None:
		moduleName = moduleName[1:]
	
	# Fill out the template contents
	template = template.replace('${VERSION}', __version__)
	template = template.replace('${MODULE}', moduleName)
	
	# Create a directory for the generated module
	moduleDir = join(args.outdir, moduleName)
	os.makedirs(moduleDir)
	
	# Create the .Build.cs file for the generated module
	buildFile = join(moduleDir, '{}.Build.cs'.format(moduleName))
	ConanTools.save(buildFile, template)
	
	# Create an empty Conanfile for the generated module
	conanfile = join(moduleDir, 'conanfile.txt')
	ConanTools.save(conanfile, '[requires]\n\n[generators]\njson\n')
	
	# Create a .gitignore file to exclude Conan-generated files from version control
	gitignore = join(moduleDir, '.gitignore')
	ConanTools.save(gitignore, '# Conan generated files\nconanbuildinfo.*\nconaninfo.*\n')
	
	# Inform the user that generation succeeded
	print('Generated boilerplate for module "{}" in "{}"'.format(moduleName, moduleDir))
