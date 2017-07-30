"""This module lets decode data according to the Bencoding specification."""


def decode(value):  # noqa: C901
    """Return the decoded value."""
    if not isinstance(value, bytes):
        raise TypeError('object of type {0} cannot be decoded'.format(type(value)))
    elif value == b'':
        raise ValueError('value is empty')

    next_pos = 0
    last_pos = len(value)

    def _unknown_type():
        raise ValueError('unknown type selector 0x{0:02X}'.format(value[next_pos]))

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
        next_pos += 1
        while next_pos < last_pos:
            if value[next_pos] == ord('e'):
                next_pos += 1
                return result
            result.append(_decode_item())

        raise ValueError('missing list value terminator')

    def _decode_dict():
        nonlocal next_pos

        result = {}
        next_pos += 1
        while next_pos < last_pos:
            if value[next_pos] == ord('e'):
                next_pos += 1
                return result
            key = _decode_item()
            if not isinstance(key, bytes):
                raise ValueError('unsupported key type {0}'.format(type(key)))
            elif key in result:
                raise ValueError('duplicate key {0}'.format(key))
            result[key] = _decode_item()

        raise ValueError('missing dict value terminator')

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

    result = _decode_item()
    if next_pos != last_pos:
        raise ValueError('extra bytes at the end')

    return result
