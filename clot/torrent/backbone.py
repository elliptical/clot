"""This module implements the torrent's underlying storage."""


import json

from .. import bencode


class _JsonEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, bytes):
            try:
                return o.decode()
            except UnicodeDecodeError:
                return 'hex::' + o.hex()
        return super().default(o)


class Backbone:
    """Torrent file low-level contents."""

    def __init__(self, raw_bytes, file_path=None):
        """Initialize self."""
        self.data = bencode.decode(raw_bytes, keytostr=True)
        if not isinstance(self.data, dict):
            raise ValueError(f'expected top-level dictionary instead of {type(self.data)}')
        self.file_path = file_path

    def save_as(self, file_path, *, overwrite=False):
        """Write the torrent to a file and remember the new path and contents on success."""
        raw_bytes = bencode.encode(self.data)
        with open(file_path, 'wb' if overwrite else 'xb') as file:
            file.write(raw_bytes)
        self.file_path = file_path

    def save(self):
        """Write the torrent to the file from which it was previously loaded or saved to."""
        if self.file_path is None:
            raise Exception('expected a torrent loaded from file')

        raw_bytes = bencode.encode(self.data)
        with open(self.file_path, 'wb') as file:
            file.write(raw_bytes)

    def dump(self, file_path, *, indent=None, sort_keys=False, overwrite=False):
        """Write the torrent to a file in JSON format."""
        with open(file_path, 'w' if overwrite else 'x', encoding='utf-8') as file:
            json.dump(self.data, file, cls=_JsonEncoder, ensure_ascii=False,
                      indent=indent, sort_keys=sort_keys)
