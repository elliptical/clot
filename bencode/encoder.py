"""This module lets encode data according to the Bencoding specification."""


import functools
import sys


_USE_BYTES_INTERPOLATION = sys.version_info >= (3, 5)


def encode(value):
    """Return the encoded value or raise an error on unsupported types."""
    return b''.join(iterencode(value))


@functools.singledispatch
def iterencode(value):
    """Yield bencoding parts for the value or raise an error on unsupported types."""
    raise TypeError('object of type {0} cannot be encoded'.format(type(value)))


if _USE_BYTES_INTERPOLATION:
    @iterencode.register(bytes)
    def _encode_bytes(value):
        value_length = len(value)
        yield b'%d' % value_length
        yield b':'
        if value_length > 0:
            yield value

    @iterencode.register(int)
    def _encode_int(value):
        yield b'i'
        yield b'%d' % value
        yield b'e'
else:   # pragma: no cover (because we do not run code coverage with Python 3.4)
    @iterencode.register(bytes)
    def _encode_bytes(value):
        value_length = len(value)
        yield str(value_length).encode('ascii')
        yield b':'
        if value_length > 0:
            yield value

    @iterencode.register(int)
    def _encode_int(value):
        yield b'i'
        yield str(value).encode('ascii')
        yield b'e'


@iterencode.register(bool)
def _encode_bool(value):
    yield b'i'
    yield b'1' if value else b'0'
    yield b'e'


@iterencode.register(tuple)
@iterencode.register(list)
def _encode_list(values):
    yield b'l'
    for value in values:
        yield from iterencode(value)
    yield b'e'


@iterencode.register(dict)
def _encode_dict(values):
    yield b'd'
    for key, value in sorted(_iter_dict_check_keys(values)):
        yield from iterencode(key)
        yield from iterencode(value)
    yield b'e'


def _iter_dict_check_keys(values):
    """Yield (key, value) pairs from a dict while ensuring keys being of bytes type."""
    for key, value in values.items():
        if not isinstance(key, bytes):
            raise TypeError('invalid key type {0}'.format(type(key)))
        yield key, value
