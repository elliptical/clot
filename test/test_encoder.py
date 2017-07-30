import tcm

import bencode


class EncodeTestCase(tcm.TestCase):
    @tcm.values(
        # pylint:disable=bad-whitespace

        # Bytes
        (b'',           b'0:'),             # empty byte string (the colon is still present)
        (b'spam\x00',   b'5:spam\x00'),     # no special treatment for the terminating zero
        (b'1234567890', b'10:1234567890'),  # length is base 10

        # Strings (encoded as UTF-8 bytes)
        ('',            b'0:'),
        ('spam\x00',    b'5:spam\x00'),
        ('1234567890',  b'10:1234567890'),

        ('\N{PILE OF POO}', b'4:\xF0\x9F\x92\xA9'),     # single character with 4-byte long UTF-8

        # Integers
        (0,     b'i0e'),
        (1,     b'i1e'),
        (-1,    b'i-1e'),
        (10,    b'i10e'),
        (-10,   b'i-10e'),

        ((1 << 64) - 1, b'i18446744073709551615e'),     # 64-bit unsigned int is supported

        # Booleans (encoded as integers)
        (False, b'i0e'),
        (True,  b'i1e'),

        # Lists
        ([],                    b'le'),                 # empty list
        ([b'spam', b'eggs'],    b'l4:spam4:eggse'),     # list of homogeneous values
        ([{b'x': []}, [-10]],   b'ld1:xleeli-10eee'),   # heterogeneous values are also OK

        # Tuples (encoded as lists)
        ((),                    b'le'),
        ((b'spam', b'eggs'),    b'l4:spam4:eggse'),

        # Dictionaries
        ({},                                    b'de'),
        ({b'cow': b'moo', 'spam': b'eggs'},     b'd3:cow3:moo4:spam4:eggse'),
        ({b'cow': [b'moo'], 'answer': 42},      b'd6:answeri42e3:cowl3:mooee'),
    )
    def test_good_values_are_encoded(self, value, expected_result):
        result = bencode.encode(value)
        self.assertEqual(result, expected_result)

    @tcm.values(
        None,
        bytearray(),
        1.2,
        3j,
    )
    def test_bad_values_will_raise(self, value):
        with self.assertRaises(TypeError) as outcome:
            bencode.encode(value)
        message = outcome.exception.args[0]
        self.assertIn('cannot be encoded', message)

    @tcm.values(
        {None: 'x'},
        {10: 'x'},
    )
    def test_bad_keys_will_raise(self, value):
        with self.assertRaises(TypeError) as outcome:
            bencode.encode(value)
        message = outcome.exception.args[0]
        self.assertIn('key type', message)

    @tcm.values(
        {'x': 1, b'x': 2},
    )
    def test_duplicate_keys_will_raise(self, value):
        with self.assertRaises(ValueError) as outcome:
            bencode.encode(value)
        message = outcome.exception.args[0]
        self.assertEqual(message, 'duplicate key x')


class IterEncodeTestCase(tcm.TestCase):
    @tcm.values(
        # pylint:disable=bad-whitespace,bad-continuation

        # Bytes
        (b'',       (b'0', b':')),
        (b'spam',   (b'4', b':', b'spam')),

        # Integers
        (0,         (b'i', b'0', b'e')),
        (-1,        (b'i', b'-1', b'e')),

        # Lists
        ([],                (b'l', b'e')),
        ([b'spam', [-10]],  (b'l', b'4', b':', b'spam', b'l', b'i', b'-10', b'e', b'e', b'e')),

        # Dictionaries
        ({},
            (b'd', b'e')),

        ({b'cow': [b'moo'], b'answer': 42},
            (b'd',
             b'6', b':', b'answer', b'i', b'42', b'e',
             b'3', b':', b'cow', b'l', b'3', b':', b'moo', b'e',
             b'e')),
    )
    def test_good_values_yield_parts(self, value, expected_result):
        result = tuple(bencode.iterencode(value))
        self.assertTupleEqual(result, expected_result)
