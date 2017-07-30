import tcm

import bencode


class DecodeTestCase(tcm.TestCase):
    @tcm.values(
        # pylint:disable=bad-whitespace

        # Bytes
        (b'0:',             b''),
        (b'1:1',            b'1'),
        (b'2:12',           b'12'),
        (b'3:123',          b'123'),
        (b'4:1234',         b'1234'),
        (b'5:12345',        b'12345'),
        (b'6:123456',       b'123456'),
        (b'7:1234567',      b'1234567'),
        (b'8:12345678',     b'12345678'),
        (b'9:123456789',    b'123456789'),
        (b'10:1234567890',  b'1234567890'),

        (b'4:spam',         b'spam'),

        # Integers
        (b'i0e',     0),
        (b'i1e',     1),
        (b'i-1e',   -1),
        (b'i10e',   10),
        (b'i-10e', -10),
        (b'i18446744073709551615e', 0xFFFFFFFFFFFFFFFF),

        # Lists
        (b'le',                 []),
        (b'l4:spam4:eggse',     [b'spam', b'eggs']),
        (b'l4:spamli-10eee',    [b'spam', [-10]]),

        # Dictionaries
        (b'de',                         {}),
        (b'd3:cow3:moo4:spam4:eggse',   {b'cow': b'moo',   b'spam': b'eggs'}),
        (b'd6:answeri42e3:cowl3:mooee', {b'cow': [b'moo'], b'answer': 42}),
    )
    def test_good_values_are_decoded(self, value, expected_result):
        result = bencode.decode(value)
        self.assertEqual(result, expected_result)

    @tcm.values(
        # pylint:disable=bad-whitespace
        (b'd4:spam4:eggse',             {'spam': b'eggs'}),
        (b'd4:\xF0\x9F\x92\xA9i0ee',    {'\N{PILE OF POO}': 0}),
    )
    def test_good_keys_are_decoded_in_keytostr_mode(self, value, expected_result):
        result = bencode.decode(value, keytostr=True)
        self.assertEqual(result, expected_result)

    @tcm.values(
        # pylint:disable=bad-whitespace

        (None,          TypeError, 'cannot be decoded'),
        (bytearray(),   TypeError, 'cannot be decoded'),
        ('',            TypeError, 'cannot be decoded'),
        ([],            TypeError, 'cannot be decoded'),
        ({},            TypeError, 'cannot be decoded'),
        (b'',           ValueError, 'value is empty'),
        (b'x',          ValueError, 'unknown type selector 0x78'),

        # Bytes
        (b'0',          ValueError, 'missing data size delimiter'),
        (b'00:',        ValueError, 'malformed data size'),
        (b'0 :',        ValueError, 'malformed data size'),
        (b'0:x',        ValueError, 'extra bytes at the end'),
        (b'2:x',        ValueError, 'wrong data size'),
        (b'2.:x',       ValueError, 'invalid literal for int'),

        # Integers
        (b'ie',         ValueError, 'invalid literal for int'),
        (b'i e',        ValueError, 'invalid literal for int'),
        (b'i0',         ValueError, 'missing int value terminator'),
        (b'i03e',       ValueError, 'malformed int value'),
        (b'i-0e',       ValueError, 'malformed int value'),
        (b'i 1 e',      ValueError, 'malformed int value'),
        (b'i0e-',       ValueError, 'extra bytes at the end'),

        # Lists
        (b'l e',        ValueError, 'unknown type selector 0x20'),
        (b'le-',        ValueError, 'extra bytes at the end'),
        (b'l',          ValueError, 'missing list value terminator'),

        # Dictionaries
        (b'd e',        ValueError, 'unknown type selector 0x20'),
        (b'de-',        ValueError, 'extra bytes at the end'),
        (b'd',          ValueError, 'missing dict value terminator'),
        (b'd3:cowe',    ValueError, 'unknown type selector 0x65'),
        (b'd3:cowi0e3:cowi0ee', ValueError, 'duplicate key'),
        (b'di0e3:cowe', ValueError, 'unsupported key type'),
    )
    def test_bad_values_will_raise(self, value, expected_exception_type, expected_message):
        with self.assertRaises(expected_exception_type) as outcome:
            bencode.decode(value)
        message = outcome.exception.args[0]
        self.assertIn(expected_message, message)

    @tcm.values(
        # pylint:disable=bad-whitespace
        (b'd4:\x80i0ee',                ValueError, 'not a UTF-8 key'),     # invalid first byte
        (b'd4:\xF0\x82\x82\xACi0ee',    ValueError, 'not a UTF-8 key'),     # overlong encoding
    )
    def test_bad_keys_will_raise_in_keytostr_mode(self, value, expected_exception_type, expected_message):
        with self.assertRaises(expected_exception_type) as outcome:
            bencode.decode(value, keytostr=True)
        message = outcome.exception.args[0]
        self.assertIn(expected_message, message)
