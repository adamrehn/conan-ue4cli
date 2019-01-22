from setuptools import setup

setup(
	name='conan-ue4cli',
	version='0.0.10',
	description='ue4cli plugin providing Conan wrapper package functionality',
	classifiers=[
		'License :: OSI Approved :: MIT License',
		'Programming Language :: Python :: 3.5',
		'Programming Language :: Python :: 3.6',
		'Programming Language :: Python :: 3.7',
		'Topic :: Software Development :: Build Tools',
		'Environment :: Console'
	],
	keywords='epic unreal engine',
	url='http://github.com/adamrehn/conan-ue4cli',
	author='Adam Rehn',
	author_email='adam@adamrehn.com',
	license='MIT',
	packages=['conan_ue4cli'],
	zip_safe=False,
	python_requires = '>=3.5',
	install_requires = [
		'conan>=1.7.4',
		'natsort>=4.0.0',
		'networkx',
		'setuptools',
		'ue4cli>=0.0.24',
		'wheel'
	],
	package_data = {
		'conan_ue4cli': [
			'*/*.py',
			'*/*/*.py',
			'*/*/*/*.py'
		]
	},
	entry_points = {
		'ue4cli.plugins': ['conan=conan_ue4cli:__PLUGIN_DESCRIPTOR__']
	}
)
