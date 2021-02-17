"""This module lets decode data according to the Bencoding specification."""


def decode(value, *, keytostr=False):   # noqa: C901 pylint: disable=too-many-statements
    """Return the decoded value."""
    if not isinstance(value, bytes):
        raise TypeError(f'object of type {type(value)} cannot be decoded')
    if value == b'':
        raise ValueError('value is empty', 0)

    next_pos = 0
    last_pos = len(value)

    def _unknown_type():
        raise ValueError(f'unknown type selector 0x{value[next_pos]:02X}')

    def _decode_bytes():
        nonlocal next_pos

        start = next_pos
        end = value.find(b':', start + 1)
        if end < 0:
            raise ValueError('missing data size delimiter')
        size = int(value[start:end])
        if len(str(size)) != end - start:
            # There were leading zeroes and/or trailing spaces there.
            raise ValueError('malformed data size')

        start = end + 1
        end = start + size
        if end > last_pos:
            raise ValueError('wrong data size')
        result = value[start:end]

        next_pos = end
        return result

    def _decode_int():
        nonlocal next_pos

        start = next_pos + 1
        end = value.find(b'e', start)
        if end < 0:
            raise ValueError('missing int value terminator')
        result = int(value[start:end])
        if len(str(result)) != end - start:
            # There were spaces, leading zeroes, or a plus sign there.
            raise ValueError('malformed int value')

        next_pos = end + 1
        return result

    def _decode_list():
        nonlocal next_pos

        result = []
        list_pos = next_pos
        next_pos += 1
        while next_pos < last_pos:
            if value[next_pos] == ord('e'):
                next_pos += 1
                return result
            result.append(_decode_item())

        raise ValueError('missing list value terminator', list_pos)

    def _decode_dict():
        nonlocal next_pos

        result = {}
        dict_pos = next_pos
        next_pos += 1
        while next_pos < last_pos:
            if value[next_pos] == ord('e'):
                next_pos += 1
                return result
            key_pos = next_pos
            key = _decode_item()
            if not isinstance(key, bytes):
                raise ValueError(f'unsupported key type {type(key)}', key_pos)
            if keytostr:
                try:
                    key = key.decode()
                except UnicodeDecodeError as ex:
                    raise ValueError(f'not a UTF-8 key {key}', key_pos) from ex
            if key in result:
                raise ValueError(f'duplicate key {key}', key_pos)
            result[key] = _decode_item()

        raise ValueError('missing dict value terminator', dict_pos)

    selector = {
        ord('0'): _decode_bytes,
        ord('1'): _decode_bytes,
        ord('2'): _decode_bytes,
        ord('3'): _decode_bytes,
        ord('4'): _decode_bytes,
        ord('5'): _decode_bytes,
        ord('6'): _decode_bytes,
        ord('7'): _decode_bytes,
        ord('8'): _decode_bytes,
        ord('9'): _decode_bytes,
        ord('i'): _decode_int,
        ord('l'): _decode_list,
        ord('d'): _decode_dict,
    }

    def _decode_item():
        return selector.get(value[next_pos], _unknown_type)()

    try:
        result = _decode_item()
        if next_pos != last_pos:
            raise ValueError('extra bytes at the end')
    except ValueError as ex:
        # Append the error location unless already present
        if len(ex.args) == 1:
            ex.args += (next_pos,)
        raise

    return result
