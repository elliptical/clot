"""This module implements a descriptor to handle torrent fields."""


class Field:
    """Field with specific type and unrestricted values, including None."""

    def __init__(self, key, value_type):
        """Initialize self."""
        self.key = key
        self.value_type = value_type

    def __set_name__(self, owner, name):
        """Customize the name used to store the field value."""
        # pylint: disable=attribute-defined-outside-init
        self.name = name
        self.private_name = '_' + name

    def __get__(self, instance, owner=None):
        """Return the field value from the specified instance (or the descriptor itself)."""
        if instance is None:
            return self

        try:
            return getattr(instance, self.private_name)
        except AttributeError:
            return self.load_from(instance)

    def __set__(self, instance, value):
        """Set the field value in the specified instance."""
        if value is not None:
            self.validate(value)
        setattr(instance, self.private_name, value)

    def load_from(self, instance):
        """Initialize the field value from the instance data dictionary."""
        try:
            value = instance.data[self.key]
        except KeyError:
            value = None
        else:
            self.validate(value)
            del instance.data[self.key]

        setattr(instance, self.private_name, value)
        return value

    def save_to(self, instance):
        """Update the instance data dictionary with the field value."""
        try:
            value = getattr(instance, self.private_name)
        except AttributeError:
            pass
        else:
            if value is None:
                instance.data.pop(self.key, None)
            else:
                instance.data[self.key] = value

    def validate(self, value):
        """Raise an exception on unexpected value type."""
        if not isinstance(value, self.value_type):
            raise TypeError(f'{self.name}: expected {value!r} to be of type {self.value_type}')
