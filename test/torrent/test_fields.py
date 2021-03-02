import tcm

from clot.torrent.fields import Field


class Base:
    def __init__(self, **kwargs):
        self.data = kwargs


class FieldTestCase(tcm.TestCase):
    def test_property_itself_is_accessible(self):
        class Dummy(Base):
            field = Field('x', int)

        self.assertIsInstance(Dummy.field, Field)

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
