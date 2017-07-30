"""This package provides a codec for bencoded data.

The official Bencoding specification can be found at the following address:
https://wiki.theory.org/index.php/BitTorrentSpecification#Bencoding
"""


__version__ = '0.0.1'


from .encoder import encode, iterencode     # noqa: F401
