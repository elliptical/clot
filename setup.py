"""Setup script.

Run "python setup.py install" to install the bencode package.
"""


import os
import re
import sys

from setuptools import setup


PACKAGE_NAME = 'bencode'


if sys.version_info < (3, 5):
    raise RuntimeError('ERROR: {} requires Python 3.5 or higher'.format(PACKAGE_NAME))


def get_version():
    """Return the version string from the package's __init__.py file."""
    with open(os.path.join(PACKAGE_NAME, '__init__.py')) as version_file:
        version_source = version_file.read()
    version_match = re.search(r"^__version__ = '([^']*)'", version_source, re.MULTILINE)
    if not version_match:
        raise RuntimeError('Could not find the version string.')
    return version_match.group(1)


VERSION = get_version()


setup(
    name=PACKAGE_NAME,
    author='Andrei Boulgakov',
    author_email='andrei.boulgakov@outlook.com',
    url='https://github.com/elliptical/bencode',
    download_url='https://github.com/elliptical/%s/archive/%s.tar.gz' % (PACKAGE_NAME, VERSION),
    license='MIT',
    platforms='All',
    description='Bencoding helpers',
    version=VERSION,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython',
    ],
    keywords=[
        'python',
        'python3',
        'bencode',
    ],
    python_requires='>=3.5',
    packages=[PACKAGE_NAME],
    zip_safe=True,
)
