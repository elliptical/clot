"""Setup script.

Run "python setup.py install" to install the clot package.
"""


from os import path
import re
import sys

from setuptools import find_packages, setup


PACKAGE_NAME = 'clot'


if sys.version_info < (3, 8):
    raise RuntimeError(f'{PACKAGE_NAME} requires Python 3.8 or higher')


def get_readme():
    """Return the contents of the package's README.md file excluding the badges row."""
    with open_text_file('README.md') as readme_file:
        text = readme_file.read()
    h1_pos = text.index('\n#') + 1
    return text[h1_pos:]


def get_version():
    """Return the version string from the package's __init__.py file."""
    with open_text_file(PACKAGE_NAME, '__init__.py') as version_file:
        version_source = version_file.read()
    version_match = re.search(r"^__version__ = '([^']*)'", version_source, re.MULTILINE)
    if not version_match:
        raise RuntimeError('Could not find the version string.')
    return version_match.group(1)


def open_text_file(*path_segments):
    """Open the specified UTF-8 encoded file relative to setup.py location."""
    my_dir = path.abspath(path.dirname(__file__))
    return open(path.join(my_dir, *path_segments), encoding='utf-8')


VERSION = get_version()


setup(
    name=PACKAGE_NAME,
    author='Andrei Boulgakov',
    author_email='andrei.boulgakov@outlook.com',
    url=f'https://github.com/elliptical/{PACKAGE_NAME}',
    download_url=f'https://github.com/elliptical/{PACKAGE_NAME}/archive/{VERSION}.tar.gz',
    license='MIT',
    platforms='All',
    description='Bencoding helpers',
    long_description=get_readme(),
    long_description_content_type='text/markdown',
    version=VERSION,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: Implementation :: CPython',
    ],
    keywords=[
        'bencode',
        'torrent',
    ],
    python_requires='>=3.8',
    packages=find_packages(),
    zip_safe=True,
)
