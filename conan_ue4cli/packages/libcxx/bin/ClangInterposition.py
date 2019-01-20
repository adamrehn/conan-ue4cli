import os, shlex, subprocess, sys
from conans import tools

def interpose(cxx):
	
	# Filter out any `-stdlib=<LIB>` flags from the supplied command-line arguments
	args = list([arg for arg in sys.argv[1:] if arg.startswith("-stdlib=") == False])
	
	# Prepend our custom compiler flags
	args = shlex.split(os.environ["CLANG_INTERPOSE_CXXFLAGS"]) + ["-Wno-unused-command-line-argument"] + args
	
	# If this is a link invocation, append our custom linker flags
	if '---link' in args:
		args = list([arg for arg in args if arg != '---link'])
		args.extend(shlex.split(os.environ["CLANG_INTERPOSE_LDFLAGS"]))
	
	# Forward all arguments to the real clang executable
	realClang = tools.which(os.environ["REAL_CXX"] if cxx == True else os.environ["REAL_CC"])
	sys.exit(subprocess.call([realClang] + args))
