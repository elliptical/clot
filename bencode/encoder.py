"""This module lets encode data according to the Bencoding specification."""


import functools


def encode(value, *, strict=False):
    """Return the encoded value or raise an error on unsupported types."""
    return b''.join(iterencode(value, strict=strict))


def iterencode(value, *, strict=False):     # noqa: C901
    """Yield bencoding parts for the value or raise an error on unsupported types."""
    location = []

    @functools.singledispatch
    def func(value):    # pylint:disable=missing-docstring
        raise TypeError('object of type {0} cannot be encoded'.format(type(value)), location)

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

    @func.register(bool)
    def _encode_bool(value):        # pylint:disable=unused-variable
        yield b'i'
        yield b'1' if value else b'0'
        yield b'e'

    @func.register(list)
    def _encode_list(values):       # pylint:disable=unused-variable
        yield b'l'
        for index, value in enumerate(values):
            location.append(index)
            yield from func(value)
            location.pop()
        yield b'e'

    @func.register(dict)
    def _encode_dict(values):       # pylint:disable=unused-variable
        yield b'd'
        last_encoded_key = None
        for encoded_key, _, value, key in sorted(_iter_dict_check_keys(values)):
            if encoded_key == last_encoded_key:
                raise ValueError('duplicate key {0}'.format(key), location)
            last_encoded_key = encoded_key
            location.append(key)
            yield from _encode_bytes(encoded_key)
            yield from func(value)
            location.pop()
        yield b'e'

    def _iter_dict_check_keys(values):
        """Yield (key, value) pairs from a dict while ensuring keys being of bytes type."""
        for key, value in values.items():
            # For consistency in error reporting, let bytes go before str
            # in case of duplicate keys.  The error message will refer to
            # the str key then.
            if isinstance(key, bytes):
                yield key, 0, value, key
            elif not strict and isinstance(key, str):
                yield key.encode(), 1, value, key
            else:
                raise TypeError('invalid key type {0}'.format(type(key)), location)

    if not strict:
        func.register(str, lambda x: _encode_bytes(x.encode()))
        func.register(tuple, _encode_list)

    yield from func(value)
