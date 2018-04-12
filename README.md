Conan ue4cli wrapper packages
=============================

The script in this repository generates Conan packages that wrap [ue4cli](https://github.com/adamrehn/ue4cli) in order to provide the compiler flags required to build against the third-party libraries that are bundled in the `Engine/Source/ThirdParty` subdirectory of the Unreal Engine 4 source tree. 

**For an example of how to use the generated packages in a UE4 project, see the [ue4-opencv-demo](https://github.com/adamrehn/ue4-opencv-demo) repository.**

**You can find the full details of the conan-ue4cli workflow in this article: <http://adamrehn.com/articles/cross-platform-library-integration-in-unreal-engine-4/>.**


Prerequisites
-------------

The generator script has the following requirements:

- The [ue4cli](https://github.com/adamrehn/ue4cli) and [Conan](https://conan.io/) Python packages from PyPI
- Unreal Engine 4.19.0 or newer
- Clang 3.8 or newer (only required under Linux)

To install the script's Python dependencies, run:

```
pip3 install -r requirements.txt
```


Installation
------------

To generate and install the wrapper scripts, simply run:

```
python3 ./generate.py
```

A Conan profile named `ue4` will be created to maintain clean separation from the default Conan profile, and wrapper packages for all of the third-party libraries bundled with the detected UE4 installation will be generated and installed into the local Conan cache.

Be sure to specify `--profile ue4` when building packages that depend on the generated wrappers, to ensure the correct compiler settings are used (e.g using clang instead of GCC under Linux.)
