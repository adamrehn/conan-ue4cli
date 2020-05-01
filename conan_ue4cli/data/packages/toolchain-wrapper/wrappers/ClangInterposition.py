import os, subprocess, sys

def _run(command, verbose):
    if verbose == True:
        print(command, file=sys.stderr)
    return subprocess.call(command)

def interpose(cxx):
    
    # Retrieve our libc++ and sysroot directories from our environment variables
    libcxx = os.environ["WRAPPED_LIBCXX"]
    sysroot = os.environ["WRAPPED_SYSROOT"]
    
    # Determine if verbose output is enabled (useful when debugging the wrappers themselves)
    verbose = os.environ.get("VERBOSE_WRAPPER", "").lower() in ["1", "true"]
    
    # Filter out any `-stdlib=<LIB>` flags from the supplied command-line arguments
    args = list([arg for arg in sys.argv[1:] if arg.startswith("-stdlib=") == False])
    
    # Apply common compiler flags
    args.extend([
        "-Wno-unused-command-line-argument",
        "--sysroot={}".format(sysroot),
        "-B{}/usr/lib".format(sysroot),
        "-B{}/usr/lib64".format(sysroot),
        "-fPIC"
    ])
    
    # Apply C++-specific compiler flags
    if cxx == True:
        args.extend([
            "-I{}/include".format(libcxx),
            "-I{}/include/c++/v1".format(libcxx),
            "-nostdinc++"
        ])
    
    # Apply verbose compiler flags (if requested)
    if verbose == True:
        args.extend(["-v"])
    
    # If this is a link invocation, append our custom linker flags
    if "---link" in args:
        
        # Filter out our linker sentinel flag
        args = list([arg for arg in args if arg != "---link"])
        
        # Some versions of some build systems (such as autotools) may erroneously prefix fully-qualified library
        # file paths with `-l`, so these prefixes need to be removed to ensure the correct linker behaviour
        prefixed = [arg for arg in args if arg.startswith("-l") and "." in os.path.basename(arg)]
        args = list([arg for arg in args if arg not in prefixed])
        args.extend([lib[2:] for lib in prefixed])
        
        # Apply common linker flags
        args.extend([
            "-L{}/usr/lib".format(sysroot),
            "-L{}/usr/lib64".format(sysroot),
            "-fuse-ld=lld",
            "-nodefaultlibs",
            "-lm",
            "-lc",
            "-lgcc_s",
            "-lgcc"
        ])
        
        # Apply C++-specific linker flags
        if cxx == True:
            args.extend([
                "{}/lib/libc++.a".format(libcxx),
                "{}/lib/libc++abi.a".format(libcxx)
            ])
        
        # Apply verbose linker flags (if requested)
        if verbose == True:
            args.extend([
                "-Wl,--verbose",
                "-Wl,--trace"
            ])
    
    # Forward all arguments to the real clang executable
    clang = os.environ["WRAPPED_CXX"] if cxx == True else os.environ["WRAPPED_CC"]
    sys.exit(_run([clang] + args, verbose))
