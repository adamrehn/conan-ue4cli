Integrate third-party libraries into the Unreal Engine with Conan
=================================================================

The conan-ue4cli Python package is a plugin for [ue4cli](https://github.com/adamrehn/ue4cli) that provides functionality for integrating third-party libraries into Unreal Engine projects and plugins using the [Conan C++ package management system](https://conan.io/). conan-ue4cli extends Conan for use with the Unreal Engine by providing functionality to facilitate the following workflow:

1. Conan packages are generated to wrap all Unreal-bundled third-party libraries, as well as the compiler toolchain itself when targeting Linux platforms.

2. Conan profiles are generated to ensure user packages are built with the correct configuration and against the wrapper packages for the Unreal-bundled versions of any dependency libraries.

3. Packages are built using the generated profiles.

4. Boilerplate code is generated for External Modules that consume the built Conan packages.

5. Optionally, precomputed dependency data is generated for one or more target platforms so Unreal projects or plugins that consume third-party libraries can be shared with other developers who do not have conan-ue4cli installed.

**Check out the [comprehensive documentation](https://adamrehn.com/docs/conan-ue4cli/) to read about the issues that conan-ue4cli addresses and for detailed instructions on installation and usage.**

Resources:

- **Documentation:** <https://adamrehn.com/docs/conan-ue4cli/>
- **GitHub repository:** <https://github.com/adamrehn/conan-ue4cli>
- **Package on PyPI:** <https://pypi.org/project/conan-ue4cli/>
- **Related articles:** <https://adamrehn.com/articles/tag/Unreal%20Engine/>

## Legal

Copyright &copy; 2018-2020, Adam Rehn. Licensed under the MIT License, see the file [LICENSE](https://github.com/adamrehn/conan-ue4cli/blob/master/LICENSE) for details.
