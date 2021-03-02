"""This module implements field type and value validators."""


from abc import ABC, abstractmethod


# pylint: disable=too-few-public-methods,no-member


class Validator(ABC):
    """Base class to validate field types and values."""

    def __init__(self, **kwargs):
        """Initialize self."""
        # Report unexpected arguments.
        if kwargs:
            raise TypeError(f'unexpected arguments: {kwargs}')

    @abstractmethod
    def validate(self, value):
        """Validate the value before assignment."""
        # Stop the chain of validations calls.


class Typed(Validator):
    """Validates the value being of specific type."""

    def __init__(self, value_type, **kwargs):
        """Initialize self."""
        self.value_type = value_type
        super().__init__(**kwargs)

    def validate(self, value):
        """Raise an exception on unexpected value type."""
        if not isinstance(value, self.value_type):
            raise TypeError(f'{self.name}: expected {value!r} to be of type {self.value_type}')
        super().validate(value)


class Bounded(Validator):
    """Validates the value against the lower and/or upper bounds."""

    def __init__(self, min_value=None, max_value=None, **kwargs):
        """Initialize self."""
        self.min_value = min_value
        self.max_value = max_value
        super().__init__(**kwargs)

    def validate(self, value):
        """Raise an exception if the value is not within the range."""
        if self.min_value is not None and value < self.min_value:
            raise ValueError(f'{self.name}: expected {value} to be at least {self.min_value}')
        if self.max_value is not None and value > self.max_value:
            raise ValueError(f'{self.name}: expected {value} to be at most {self.max_value}')
        super().validate(value)
