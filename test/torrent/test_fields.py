import tcm

from clot.torrent.fields import Bytes, Field, Integer, Layout


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


class BytesTestCase(tcm.TestCase):
    def test_value_type_is_enforced(self):
        class Dummy(Base):
            field = Bytes('x')

        dummy = Dummy()
        dummy.field = b'123'
        self.assertEqual(dummy.field, b'123')

        with self.assertRaises(TypeError) as outcome:
            dummy.field = 0
        message = outcome.exception.args[0]
        self.assertIn("of type <class 'bytes'>", message)
        self.assertEqual(dummy.field, b'123')

    def test_nonempty_value_is_enforced(self):
        class Dummy(Base):
            field = Bytes('x')

        dummy = Dummy()
        dummy.field = b'123'
        self.assertEqual(dummy.field, b'123')

        with self.assertRaises(ValueError) as outcome:
            dummy.field = b'\r \n \t \v \f'
        message = outcome.exception.args[0]
        self.assertIn('empty value is not allowed', message)
        self.assertEqual(dummy.field, b'123')
