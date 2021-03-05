from datetime import datetime, timezone

import tcm

from clot.torrent.fields import Bytes, Field, Integer, Layout, String, Timestamp, Url


NOW_TZ_AWARE = datetime.now(tz=timezone.utc)
NOW_NAIVE = datetime.now()

LETTER_BE = '\N{CYRILLIC CAPITAL LETTER BE}'


class Base(metaclass=Layout):
    def __init__(self, **kwargs):
        self.data = kwargs
        super().__init__()


class LayoutTestCase(tcm.TestCase):
    def test_existing_fields_attribute_will_raise(self):
        with self.assertRaises(TypeError) as outcome:
            class _Dummy(metaclass=Layout):
                _fields = None

        message = outcome.exception.args[0]
        self.assertEqual(message, "'_Dummy' already has the '_fields' attribute")

    def test_fields_can_be_loaded_at_once(self):
        class Dummy(Base):
            field_x = Field('x', int)
            field_y = Field('y', int)

        dummy = Dummy(x=1, y=2)
        dummy.load_fields()     # pylint: disable=no-member

        self.assertTrue(hasattr(dummy, '_field_x'))
        self.assertEqual(getattr(dummy, '_field_x'), 1)

        self.assertTrue(hasattr(dummy, '_field_y'))
        self.assertEqual(getattr(dummy, '_field_y'), 2)

    def test_fields_can_be_saved_at_once(self):
        class Dummy(Base):
            field_x = Field('x', int)
            field_y = Field('y', int)

        dummy = Dummy()
        dummy.field_x = 1
        dummy.field_y = 2

        self.assertDictEqual(dummy.data, {})
        dummy.save_fields()     # pylint: disable=no-member
        self.assertDictEqual(dummy.data, {'x': 1, 'y': 2})


class FieldTestCase(tcm.TestCase):
    def test_property_itself_is_accessible(self):
        class Dummy(Base):
            field = Field('x', int)

        self.assertIsInstance(Dummy.field, Field)

    def test_unknown_keyword_will_raise(self):
        with self.assertRaises(TypeError) as outcome:
            class _Dummy(Base):
                field = Field('x', int, some='stuff')
        message = outcome.exception.args[0]
        self.assertEqual(message, """unexpected arguments: {'some': 'stuff'}""")

    def test_missing_field_is_none(self):
        class Dummy(Base):
            field = Field('x', int)

        dummy = Dummy(z=3)

        self.assertFalse(hasattr(dummy, '_field'))
        value = dummy.field
        self.assertTrue(hasattr(dummy, '_field'))

        self.assertIsNone(value)
        self.assertDictEqual(dummy.data, {'z': 3})

    def test_present_field_is_auto_loaded(self):
        class Dummy(Base):
            field = Field('x', int)

        dummy = Dummy(x=1)

        self.assertFalse(hasattr(dummy, '_field'))
        value = dummy.field
        self.assertTrue(hasattr(dummy, '_field'))

        self.assertEqual(value, 1)
        self.assertDictEqual(dummy.data, {})

    def test_auto_load_will_raise_on_bad_value(self):
        class Dummy(Base):
            field = Field('x', int)

        dummy = Dummy(x='1')

        self.assertFalse(hasattr(dummy, '_field'))

        with self.assertRaises(TypeError) as outcome:
            _ = dummy.field
        message = outcome.exception.args[0]
        self.assertEqual(message, "field: expected '1' to be of type <class 'int'>")

        self.assertFalse(hasattr(dummy, '_field'))
        self.assertDictEqual(dummy.data, {'x': '1'})

    def test_data_is_not_popped_when_field_is_set(self):
        class Dummy(Base):
            field = Field('x', int)

        dummy = Dummy(x=1)

        self.assertFalse(hasattr(dummy, '_field'))
        dummy.field = 0
        self.assertTrue(hasattr(dummy, '_field'))

        self.assertEqual(dummy.field, 0)
        self.assertDictEqual(dummy.data, {'x': 1})

    @tcm.values(
        (int,   123,    '123'),
        (str,   '123',  123),
    )
    def test_value_type_is_enforced(self, value_type, good_value, bad_value):
        class Dummy(Base):
            field = Field('x', value_type)

        dummy = Dummy()
        dummy.field = good_value
        self.assertEqual(dummy.field, good_value)
        dummy.field = None
        self.assertIsNone(dummy.field)

        with self.assertRaises(TypeError) as outcome:
            dummy.field = bad_value
        message = outcome.exception.args[0]
        self.assertIn(f'of type {value_type}', message)

    def test_set_field_can_be_saved(self):
        class Dummy(Base):
            field = Field('x', int)

        dummy = Dummy(x=1)
        self.assertDictEqual(dummy.data, {'x': 1})

        # Updates existing key.
        dummy.field = 2
        Dummy.field.save_to(dummy)
        self.assertDictEqual(dummy.data, {'x': 2})

        # Deletes existing key.
        dummy.field = None
        Dummy.field.save_to(dummy)
        self.assertDictEqual(dummy.data, {})

        # Adds missing key.
        dummy.field = 3
        Dummy.field.save_to(dummy)
        self.assertDictEqual(dummy.data, {'x': 3})

    def test_not_loaded_field_does_not_raise_on_save(self):
        class Dummy(Base):
            field = Field('x', int)

        dummy = Dummy(x=1)
        Dummy.field.save_to(dummy)
        self.assertDictEqual(dummy.data, {'x': 1})


class HighLevelTypesTestCase(tcm.TestCase):
    @tcm.values(
        (Integer,   123,                    '123',  'int'),
        (Bytes,     b'123',                 123,    'bytes'),
        (String,    '123',                  123,    'str'),
        (Url,       'http://example.com',   123,    'str'),
        (Timestamp, NOW_TZ_AWARE,           123,    'datetime.datetime'),
    )
    def test_value_type_is_enforced(self, field_type, good_value, bad_value, expected_type_name):
        class Dummy(Base):
            field = field_type('x')

        dummy = Dummy()
        dummy.field = good_value
        self.assertEqual(dummy.field, good_value)

        with self.assertRaises(TypeError) as outcome:
            dummy.field = bad_value
        message = outcome.exception.args[0]
        self.assertIn(f"of type <class '{expected_type_name}'>", message)
        self.assertEqual(dummy.field, good_value)

    @tcm.values(
        (Bytes,     b'123',                 b'\r \n \t \v \f'),
        (String,    '123',                  '\r \n \t \v \f'),
        (Url,       'http://example.com',   '\r \n \t \v \f'),
    )
    def test_nonempty_value_is_enforced(self, field_type, good_value, empty_value):
        class Dummy(Base):
            field = field_type('x')

        dummy = Dummy()
        dummy.field = good_value
        self.assertEqual(dummy.field, good_value)

        with self.assertRaises(ValueError) as outcome:
            dummy.field = empty_value
        message = outcome.exception.args[0]
        self.assertIn('empty value is not allowed', message)
        self.assertEqual(dummy.field, good_value)


class IntegerTestCase(tcm.TestCase):
    def test_value_type_is_enforced(self):
        class Dummy(Base):
            field = Integer('x')

        dummy = Dummy()
        dummy.field = 123
        self.assertEqual(dummy.field, 123)

        with self.assertRaises(TypeError) as outcome:
            dummy.field = ''
        message = outcome.exception.args[0]
        self.assertIn("of type <class 'int'>", message)
        self.assertEqual(dummy.field, 123)

    @tcm.values(
        (10, 'at least 10'),
    )
    def test_min_value_is_enforced(self, min_value, expected_message):
        class Dummy(Base):
            field = Integer('x', min_value=min_value)

        dummy = Dummy()
        dummy.field = min_value
        self.assertEqual(dummy.field, min_value)
        dummy.field = min_value + 1
        self.assertEqual(dummy.field, min_value + 1)

        with self.assertRaises(ValueError) as outcome:
            dummy.field = min_value - 1
        message = outcome.exception.args[0]
        self.assertIn(expected_message, message)
        self.assertEqual(dummy.field, min_value + 1)

    @tcm.values(
        (10, 'at most 10'),
    )
    def test_max_value_is_enforced(self, max_value, expected_message):
        class Dummy(Base):
            field = Integer('x', max_value=max_value)

        dummy = Dummy()
        dummy.field = max_value
        self.assertEqual(dummy.field, max_value)
        dummy.field = max_value - 1
        self.assertEqual(dummy.field, max_value - 1)

        with self.assertRaises(ValueError) as outcome:
            dummy.field = max_value + 1
        message = outcome.exception.args[0]
        self.assertIn(expected_message, message)
        self.assertEqual(dummy.field, max_value - 1)


class StringTestCase(tcm.TestCase):
    @tcm.values(
        (1,                             TypeError,     "field: expected 1 to be of type <class 'bytes'>"),
        (LETTER_BE.encode('cp1251'),    ValueError,    r"field: cannot decode b'\xc1' as UTF-8"),
    )
    def test_bad_storage_will_raise_on_load(self, value, exception_type, expected_message):
        class Dummy(Base):
            field = String('x')

        dummy = Dummy(x=value)
        with self.assertRaises(exception_type) as outcome:
            _ = dummy.field
        message = outcome.exception.args[0]
        self.assertEqual(message, expected_message)

    def test_explicit_field_encoding_is_used(self):
        class Dummy(Base):
            normal_field = String('x')
            explicit_field = String('y', encoding='ASCII')

        dummy = Dummy(x=LETTER_BE.encode(), y=LETTER_BE.encode())
        self.assertEqual(dummy.normal_field, LETTER_BE)

        with self.assertRaises(ValueError) as outcome:
            _ = dummy.explicit_field
        message = outcome.exception.args[0]
        self.assertEqual(message, r"explicit_field: cannot decode b'\xd0\x91' as ASCII")


class UrlTestCase(tcm.TestCase):
    @tcm.values(
        (1,                     None,     TypeError,    "field: expected 1 to be of type <class 'bytes'>"),
        (b'http2://hostname',   None,     ValueError,   "field: the value 'http2://hostname' is ill-formed (unexpected scheme)"),
        (b'http://hostname',    ['ftp'],  ValueError,   "field: the value 'http://hostname' is ill-formed (unexpected scheme)"),
        (b'hostname',           [],       ValueError,   "field: the value 'hostname' is ill-formed (missing scheme)"),
        (b'hostname',           [''],     ValueError,   "field: the value 'hostname' is ill-formed (missing scheme)"),
        (b'http://:20',         None,     ValueError,   "field: the value 'http://:20' is ill-formed (missing hostname)"),
    )
    def test_malformed_string_will_raise_on_load(self, value, schemes, exception_type, expected_message):
        class Dummy(Base):
            field = Url('x', schemes=schemes)

        dummy = Dummy(x=value)
        with self.assertRaises(exception_type) as outcome:
            _ = dummy.field
        message = outcome.exception.args[0]
        self.assertEqual(message, expected_message)

    @tcm.values(
        (b'ftp://hostname',         ['ftp']),
        (b'https://hostname',       None),
        (b'http://hostname:123',    None),
        (b'udp://hostname',         None),
    )
    def test_valid_string_is_accepted(self, value, schemes):
        class Dummy(Base):
            field = Url('x', schemes=schemes)

        dummy = Dummy(x=value)
        self.assertEqual(dummy.field, value.decode())


class TimestampTestCase(tcm.TestCase):
    @tcm.values(
        (b'1',              TypeError,      "field: expected b'1' to be of type <class 'int'>"),
        (100_000_000_000,   ValueError,     'field: cannot convert 100000000000 to a timestamp'),
    )
    def test_bad_storage_will_raise_on_load(self, value, exception_type, expected_message):
        class Dummy(Base):
            field = Timestamp('x')

        dummy = Dummy(x=value)
        with self.assertRaises(exception_type) as outcome:
            _ = dummy.field
        message = outcome.exception.args[0]
        self.assertEqual(message, expected_message)

    def test_timestamp_requires_tzinfo(self):
        class Dummy(Base):
            field = Timestamp('x')

        dummy = Dummy()
        with self.assertRaises(ValueError) as outcome:
            dummy.field = NOW_NAIVE
        message = outcome.exception.args[0]
        self.assertEqual(message, f'field: the value {NOW_NAIVE!r} is missing timezone info')
