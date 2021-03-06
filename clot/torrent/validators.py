"""This module implements field type and value validators."""


from datetime import datetime, timezone
from urllib.parse import urlparse

from .layout import Validator


# pylint: disable=no-member


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


class NonEmpty(Validator):
    """Validates the value being non-empty (not whitespace only)."""

    def validate(self, value):
        """Raise an exception if the value consists of whitespace only."""
        if not value.strip():
            raise ValueError(f'{self.name}: empty value is not allowed')
        super().validate(value)


class Encoded(Validator):
    """Decodes bytes to a string value using the UTF-8 encoding."""

    def __init__(self, encoding=None, **kwargs):
        """Initialize self."""
        self.encoding = encoding
        super().__init__(**kwargs)

    def load_value(self, instance):
        """Convert bytes to string."""
        value = super().load_value(instance)
        if not isinstance(value, bytes):
            raise TypeError(f'{self.name}: expected {value!r} to be of type {bytes}')

        encodings = []
        if self.encoding:
            encodings.append(self.encoding)
        else:
            codepage = getattr(instance, 'codepage', None)
            if codepage:
                codepage = f'cp{codepage}'

            encoding = getattr(instance, 'encoding', None) or codepage
            if encoding and encoding.replace('_', '-').upper() not in ('UTF-8', 'UTF8'):
                encodings.append(encoding)
            encodings.append('UTF-8')

            fallback_encoding = getattr(instance, 'fallback_encoding', None)
            if fallback_encoding:
                encodings.append(fallback_encoding)

        for encoding in encodings:
            try:
                return value.decode(encoding)
            except UnicodeDecodeError:
                pass

        raise ValueError(f'{self.name}: cannot decode {value!r} as {" or ".join(encodings)}')


class ValidUrl(Validator):
    """Ensures the value is an URL with non-empty scheme and hostname."""

    default_schemes = (
        'https',
        'http',
        'udp',
    )

    def __init__(self, schemes=None, **kwargs):
        """Initialize self."""
        self.schemes = list(filter(None, schemes or self.default_schemes))
        super().__init__(**kwargs)

    def validate(self, value):
        """Raise an exception on nonconforming values."""
        parsed = urlparse(value)
        if not parsed.scheme.strip():
            raise ValueError(f'{self.name}: the value {value!r} is ill-formed (missing scheme)')
        if parsed.scheme not in self.schemes:
            raise ValueError(f'{self.name}: the value {value!r} is ill-formed (unexpected scheme)')
        if parsed.hostname is None or not parsed.hostname.strip():
            raise ValueError(f'{self.name}: the value {value!r} is ill-formed (missing hostname)')
        super().validate(value)


class UnixEpoch(Validator):
    """Interprets int as a timestamp in the standard Unix epoch format."""

    def load_value(self, instance):
        """Convert integer to UTC datetime."""
        value = super().load_value(instance)
        if not isinstance(value, int):
            raise TypeError(f'{self.name}: expected {value!r} to be of type {int}')

        # Interpret the value according to the standard Unix epoch format, which represents
        # the number of seconds elapsed since 1970-01-01 00:00:00 +0000 (UTC).
        try:
            return datetime.fromtimestamp(value, timezone.utc)
        except (OverflowError, OSError, ValueError) as ex:
            raise ValueError(f'{self.name}: cannot convert {value!r} to a timestamp') from ex

    def validate(self, value):
        """Raise an exception if timezone info is missing."""
        if value.tzinfo is None:
            raise ValueError(f'{self.name}: the value {value!r} is missing timezone info')
        super().validate(value)
