"""This package provides torrent-related functions and classes.

Torrent structure is described at the following address:
https://wiki.theory.org/index.php/BitTorrentSpecification#Metainfo_File_Structure
"""


from .backbone import Backbone


def new():
    """Create an empty torrent."""
    return parse(b'de')


def parse(raw_bytes):
    """Create a torrent from a bytes-like object."""
    return Backbone(raw_bytes)


def load(file_path):
    """Create a torrent from a file specified by the path-like object."""
    with open(file_path, 'rb') as readable:
        raw_bytes = readable.read()
    return Backbone(raw_bytes, file_path)
