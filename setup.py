import os
import re
try:
    from setuptools import setup
except ImportError:
    raise RuntimeError('setuptools is required')

def read_file(*paths):
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, *paths)) as f:
        return f.read()

PACKAGE = 'skewt'

SHORT_DESC = 'Plots and analyses atmospheric profile data'
VERSIONFILE= PACKAGE+"/__init__.py"
AUTHOR = "Thomas Chubb"
AUTHOR_EMAIL = 'thomas.chubb@monash.edu'
URL = 'http://pypi.python.org/pypi/SkewT/'

verstrline = open(VERSIONFILE, "rt").read()
VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
mo = re.search(VSRE, verstrline, re.M)
if mo:
    VERSION = mo.group(1)
else:
    raise RuntimeError("Unable to find version string in %s." % (VERSIONFILE,))

long_description = read_file('README.md')

# Add release history
long_description += "\n\n" + read_file('CHANGES.txt')


setup(
    name=PACKAGE,
    version=VERSION,
    description=SHORT_DESC,
    long_description=long_description,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    url=URL,
    packages=[PACKAGE],
    include_package_data=True,
    install_requires=[
        "numpy",
        "matplotlib",
    ],
    license='LICENSE.txt'
    )

