"""This module implements the torrent's underlying storage."""


from .. import bencode


class Backbone:     # pylint: disable=too-few-public-methods
    """Torrent file low-level contents."""

    def __init__(self, raw_bytes, file_path=None):
        """Initialize self."""
        self.raw_bytes = raw_bytes
        self.data = bencode.decode(raw_bytes, keytostr=True)
        if not isinstance(self.data, dict):
            raise ValueError(f'expected top-level dictionary instead of {type(self.data)}')
        self.file_path = file_path
