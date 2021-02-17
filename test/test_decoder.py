import tcm

from clot import bencode


class DecodeTestCase(tcm.TestCase):
    @tcm.values(
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
        (None,          TypeError, 'cannot be decoded'),
        (bytearray(),   TypeError, 'cannot be decoded'),
        ('',            TypeError, 'cannot be decoded'),
        ([],            TypeError, 'cannot be decoded'),
        ({},            TypeError, 'cannot be decoded'),
    )
    def test_bad_values_will_raise(self, value, expected_exception_type, expected_message):
        with self.assertRaises(expected_exception_type) as outcome:
            bencode.decode(value)
        message = outcome.exception.args[0]
        self.assertIn(expected_message, message)

    @tcm.values(
        (b'',           0, ValueError, 'value is empty'),
        (b'x',          0, ValueError, 'unknown type selector 0x78'),

        # Bytes
        (b'0',          0, ValueError, 'missing data size delimiter'),
        (b'00:',        0, ValueError, 'malformed data size'),
        (b'0 :',        0, ValueError, 'malformed data size'),
        (b'0:x',        2, ValueError, 'extra bytes at the end'),
        (b'2:x',        0, ValueError, 'wrong data size'),
        (b'2.:x',       0, ValueError, 'invalid literal for int'),

        # Integers
        (b'ie',         0, ValueError, 'invalid literal for int'),
        (b'i e',        0, ValueError, 'invalid literal for int'),
        (b'i0',         0, ValueError, 'missing int value terminator'),
        (b'i03e',       0, ValueError, 'malformed int value'),
        (b'i-0e',       0, ValueError, 'malformed int value'),
        (b'i 1 e',      0, ValueError, 'malformed int value'),
        (b'i0e-',       3, ValueError, 'extra bytes at the end'),

        # Lists
        (b'l e',        1, ValueError, 'unknown type selector 0x20'),
        (b'le-',        2, ValueError, 'extra bytes at the end'),
        (b'l',          0, ValueError, 'missing list value terminator'),

        # Dictionaries
        (b'd e',        1, ValueError, 'unknown type selector 0x20'),
        (b'de-',        2, ValueError, 'extra bytes at the end'),
        (b'd',          0, ValueError, 'missing dict value terminator'),
        (b'd3:cowe',    6, ValueError, 'unknown type selector 0x65'),
        (b'd3:cowi0e3:cowi0ee', 9, ValueError, 'duplicate key'),
        (b'di0e3:cowe', 1, ValueError, 'unsupported key type'),
    )
    def test_bad_values_will_raise_with_error_location(self, value, expected_locaton, expected_exception_type, expected_message):
        with self.assertRaises(expected_exception_type) as outcome:
            bencode.decode(value)
        message, location = outcome.exception.args
        self.assertIn(expected_message, message)
        self.assertEqual(location, expected_locaton)


class DecodeKeyToStrTestCase(tcm.TestCase):
    @tcm.values(
        (b'd4:spam4:eggse',             {'spam': b'eggs'}),
        (b'd4:\xF0\x9F\x92\xA9i0ee',    {'\N{PILE OF POO}': 0}),
    )
    def test_good_keys_are_decoded(self, value, expected_result):
        result = bencode.decode(value, keytostr=True)
        self.assertEqual(result, expected_result)

    @tcm.values(
        (b'd4:\x80i0ee',                1, ValueError, 'not a UTF-8 key'),     # invalid first byte
        (b'd4:\xF0\x82\x82\xACi0ee',    1, ValueError, 'not a UTF-8 key'),     # overlong encoding
    )
    def test_bad_keys_will_raise(self, value, expected_locaton, expected_exception_type, expected_message):
        with self.assertRaises(expected_exception_type) as outcome:
            bencode.decode(value, keytostr=True)
        message, location = outcome.exception.args
        self.assertIn(expected_message, message)
        self.assertEqual(location, expected_locaton)
