Conan ue4cli wrapper packages
=============================

The conan-ue4cli Python package is a plugin for [ue4cli](https://github.com/adamrehn/ue4cli) that provides functionality for generating and using Conan packages that wrap the third-party libraries bundled in the `Engine/Source/ThirdParty` subdirectory of the Unreal Engine 4 source tree. 

**For an example of how to use the generated packages in a UE4 project, see the [ue4-opencv-demo](https://github.com/adamrehn/ue4-opencv-demo) repository.**

**You can find the full details of the conan-ue4cli workflow in this article: <http://adamrehn.com/articles/cross-platform-library-integration-in-unreal-engine-4/>.**


Installation
-------------

To install conan-ue4cli, simply run:

```
pip3 install conan-ue4cli
```


Wrapper generation
------------------

You can perform package generation by running:

```
ue4 conan generate
```

A Conan profile named `ue4` will be created to maintain clean separation from the default Conan profile, and wrapper packages for all of the third-party libraries bundled with the detected UE4 installation will be generated and installed into the local Conan cache.

Note that you will need to use a source build of UE4 to generate wrapper packages rather than an Installed Build (such as those obtained via the Epic Games Launcher), since Installed Builds do not contain all of the files necessary for wrapper generation. Fortunately, you don't actually need to have built UE4 from source for this to work, you can simply clone the source code and run `Setup.bat`/`Setup.sh` and `GenerateProjectFiles.bat`/`GenerateProjectFiles.sh` to download the required third-party dependencies and conan-ue4cli can generate the wrappers from the source tree.


Building packages that use the wrappers
---------------------------------------

You can build packages that depend on the wrappers using the `ue4 conan build` command. By default, the current working directory will be searched for available packages to build. See the [**ue4-conan-recipes**
](https://github.com/adamrehn/ue4-conan-recipes) repository for an example of the required directory structure for packages that are built using this method.

You can also build Conan packages that depend on the wrappers using the stanard Conan commands. Be sure to specify `--profile ue4` to ensure the correct compiler settings are used (e.g using clang instead of GCC under Linux.)
