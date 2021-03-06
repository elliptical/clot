"""This module provides the foundation to load, validate and save torrent fields."""


from abc import ABC, abstractmethod


# pylint: disable=no-member


class Validator(ABC):
    """Base class to validate field types and values."""

    def __init__(self, **kwargs):
        """Initialize self."""
        # Report unexpected arguments.
        if kwargs:
            raise TypeError(f'unexpected arguments: {kwargs}')

    def load_value(self, instance):
        """Return the underlying storage value."""
        return instance.data[self.key]

    def save_value(self, instance, value):
        """Save the value to the underlying storage."""
        instance.data[self.key] = value

    def delete_value(self, instance):
        """Delete the value from the underlying storage."""
        instance.data.pop(self.key, None)

    @abstractmethod
    def validate(self, value):
        """Validate the value before assignment."""
        # Stop the chain of validations calls.


class Attr(Validator):
    """Abstract base class for fields."""

    def __init__(self, key, **kwargs):
        """Initialize self."""
        self.key = key
        self.loaded = None
        super().__init__(**kwargs)

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
            value = self.load_value(instance)
        except KeyError:
            value = None
        else:
            self.validate(value)

        self.delete_value(instance)
        self.loaded = True
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
                self.delete_value(instance)
            else:
                self.save_value(instance, value)


class Layout(type):
    """Metaclass providing methods to load and save all fields at once."""

    def __new__(cls, name, bases, mapping):
        """Create the class after expanding the original mapping."""
        fields = [value for value in mapping.values() if isinstance(value, Attr)]

        def load_fields(self):
            for field in self._fields:
                field.loaded = False

            for field in self._fields:
                # The "encoding" and "codepage" fields are indirectly loaded right
                # before loading the first encoded field.  Prevent them from being
                # loaded again; otherwise the instance data dictionary will already
                # have the associated key popped and field values become None.
                if not field.loaded:
                    field.load_from(self)

        def save_fields(self):
            for field in self._fields:
                field.save_to(self)

        new_stuff = {
            '_fields': fields,
            load_fields.__name__: load_fields,
            save_fields.__name__: save_fields,
        }

        for key in new_stuff:
            if key in mapping:
                raise TypeError(f'{name!r} already has the {key!r} attribute')

        mapping.update(new_stuff)

        return super().__new__(cls, name, bases, mapping)
