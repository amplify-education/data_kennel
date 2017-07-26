"""setup.py controls the build, testing, and distribution of the egg"""

from setuptools import setup, find_packages
import re
import os.path


VERSION_REGEX = re.compile(r"""
    ^__version__\s=\s
    ['"](?P<version>.*?)['"]
""", re.MULTILINE | re.VERBOSE)

VERSION_FILE = os.path.join("data_kennel", "version.py")


def get_long_description():
    """Reads the long description from the README"""
    with open('README.rst') as readmefile:
        return readmefile.read()


def get_version():
    """Reads the version from the package"""
    with open(VERSION_FILE) as handle:
        lines = handle.read()
        version_result = VERSION_REGEX.search(lines)
        if version_result:
            return "{0}".format(version_result.group(1))
        else:
            raise ValueError("Unable to determine __version__")


def get_requirements():
    """Reads the installation requirements from requirements.pip"""
    with open("requirements.pip") as reqfile:
        return filter(lambda line: not line.startswith(('#', '-')), reqfile.read().split("\n"))

setup(
    name='data_kennel',
    version=get_version(),
    description="Data Kennel is a CLI tool for managing Datadog infrastructure.",
    long_description=get_long_description(),
    # Get strings from http://www.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords=[
        'python',
        'datadog',
        'cli'
    ],
    author='amplify',
    author_email='astronauts.core@amplify.com',
    url='https://github.com/amplify-education/data_kennel',
    license='MIT',
    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
    zip_safe=False,
    dependency_links=[
    ],
    install_requires=get_requirements(),
    scripts=['bin/dk_monitor'],
    test_suite='nose.collector',
    entry_points="""
        [paste.app_factory]
        main=data_kennel:main
    """,
)
