"""This module lets encode data according to the Bencoding specification."""


import functools
import sys


_USE_BYTES_INTERPOLATION = sys.version_info >= (3, 5)


def encode(value):
    """Return the encoded value or raise an error on unsupported types."""
    return b''.join(iterencode(value))


def iterencode(value):  # noqa: C901
    """Yield bencoding parts for the value or raise an error on unsupported types."""
    @functools.singledispatch
    def func(value):    # pylint:disable=missing-docstring
        raise TypeError('object of type {0} cannot be encoded'.format(type(value)))

    if _USE_BYTES_INTERPOLATION:
        @func.register(bytes)
        def _encode_bytes(value):
            value_length = len(value)
            yield b'%d' % value_length
            yield b':'
            if value_length > 0:
                yield value

        @func.register(int)
        def _encode_int(value):     # pylint:disable=unused-variable
            yield b'i'
            yield b'%d' % value
            yield b'e'
    else:   # pragma: no cover (because we do not run code coverage with Python 3.4)
        @func.register(bytes)
        def _encode_bytes(value):
            value_length = len(value)
            yield str(value_length).encode('ascii')
            yield b':'
            if value_length > 0:
                yield value

        @func.register(int)
        def _encode_int(value):
            yield b'i'
            yield str(value).encode('ascii')
            yield b'e'

    @func.register(bool)
    def _encode_bool(value):        # pylint:disable=unused-variable
        yield b'i'
        yield b'1' if value else b'0'
        yield b'e'

    @func.register(str)
    def _encode_str(value):         # pylint:disable=unused-variable
        yield from _encode_bytes(value.encode())

    @func.register(tuple)
    @func.register(list)
    def _encode_list(values):       # pylint:disable=unused-variable
        yield b'l'
        for value in values:
            yield from func(value)
        yield b'e'

    @func.register(dict)
    def _encode_dict(values):       # pylint:disable=unused-variable
        yield b'd'
        last_encoded_key = None
        for encoded_key, _, value, key in sorted(_iter_dict_check_keys(values)):
            if encoded_key == last_encoded_key:
                raise ValueError('duplicate key {0}'.format(key))
            last_encoded_key = encoded_key
            yield from func(encoded_key)
            yield from func(value)
        yield b'e'

    def _iter_dict_check_keys(values):
        """Yield (key, value) pairs from a dict while ensuring keys being of bytes type."""
        for key, value in values.items():
            # For consistency in error reporting, let bytes go before str
            # in case of duplicate keys.  The error message will refer to
            # the str key then.
            if isinstance(key, str):
                yield key.encode(), 1, value, key
            elif isinstance(key, bytes):
                yield key, 0, value, key
            else:
                raise TypeError('invalid key type {0}'.format(type(key)))

    yield from func(value)
