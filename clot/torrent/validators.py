"""This module implements field type and value validators."""


from collections.abc import Iterable
from datetime import datetime, timezone
from urllib.parse import urlparse

from .layout import Validator
from .values import List


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
        return super().validate(value)


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
        return super().validate(value)


class NonEmpty(Validator):
    """Validates the value being non-empty (not whitespace only)."""

    def validate(self, value):
        """Raise an exception if the value consists of whitespace only."""
        if not value.strip():
            raise ValueError(f'{self.name}: empty value is not allowed')
        return super().validate(value)


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
        return super().validate(value)


class _UrlAware:    # pylint: disable=too-few-public-methods
    """Mixin class to decode and validate URL strings."""

    default_schemes = (
        'https',
        'http',
        'udp',
    )

    def __init__(self, schemes=None, **kwargs):
        """Initialize self."""
        self.schemes = list(filter(None, schemes or self.default_schemes))
        super().__init__(**kwargs)

    def valid_url(self, value):
        """Raise an exception on nonconforming values."""
        if isinstance(value, bytes):
            try:
                value = value.decode()
            except UnicodeDecodeError as ex:
                raise ValueError(f'{self.name}: cannot decode {value!r} as UTF-8') from ex
        elif not isinstance(value, str):
            raise TypeError(f'{self.name}: expected {value!r} to be of type {bytes} or {str}')

        parsed = urlparse(value)
        if not parsed.scheme.strip():
            raise ValueError(f'{self.name}: the value {value!r} is ill-formed (missing scheme)')
        if parsed.scheme not in self.schemes:
            raise ValueError(f'{self.name}: the value {value!r} is ill-formed (unexpected scheme)')
        if parsed.hostname is None or not parsed.hostname.strip():
            raise ValueError(f'{self.name}: the value {value!r} is ill-formed (missing hostname)')
        return value


class ValidUrl(_UrlAware, Validator):
    """Ensures the value is an URL with non-empty scheme and hostname."""

    def validate(self, value):
        """Raise an exception on nonconforming values."""
        value = self.valid_url(value)
        return super().validate(value)


class ValidUrlList(_UrlAware, Validator):
    """Ensures the value is a (possibly empty) list of URLs."""

    def save_value(self, instance, value):
        """Save the value to the underlying storage."""
        if not value:
            super().delete_value(instance)
        elif len(value) == 1:
            super().save_value(instance, value[0])
        else:
            super().save_value(instance, list(value))

    def validate(self, value):
        """Raise an exception on nonconforming values."""
        if self.__assign_as_is(value):
            pass
        elif isinstance(value, (bytes, str)):
            value = List(self.valid_url, value)
        elif isinstance(value, Iterable):
            value = List(self.valid_url, *value)
        else:
            raise TypeError(f'{self.name}: expected {value!r} to be of type'
                            f' {bytes}, {str}, {List}, or an iterable')

        return super().validate(value)

    def __assign_as_is(self, value):
        return isinstance(value, List) and value.valid_item.__func__ is self.valid_url.__func__


class ValidNodeList(Validator):
    """A possibly empty list of host and port pairs (represented by two-item lists)."""

    def save_value(self, instance, value):
        """Save the value to the underlying storage."""
        if not value:
            super().delete_value(instance)
        else:
            def split(host_port):
                host, _, port = host_port.rpartition(':')
                return host, int(port)

            super().save_value(instance, list(split(item) for item in value))

    def validate(self, value):
        """Raise an exception on nonconforming values."""
        if self.__assign_as_is(value):
            pass
        elif isinstance(value, Iterable):
            value = List(self.valid_node, *value)
        else:
            raise TypeError(f'{self.name}: expected {value!r} to be of type {List}, or an iterable')

        return super().validate(value)

    def __assign_as_is(self, value):
        return isinstance(value, List) and value.valid_item.__func__ is self.valid_node.__func__

    def valid_node(self, value):
        """Raise an exception on nonconforming values."""
        if not isinstance(value, list):
            raise TypeError(f'{self.name}: expected {value!r} to be of type {list}')

        if len(value) != 2:
            raise ValueError(f'{self.name}: expected {value!r} to contain exactly 2 items')

        host, port = value

        if isinstance(host, bytes):
            try:
                host = host.decode()
            except UnicodeDecodeError as ex:
                raise ValueError(f'{self.name}: cannot decode {host!r} as UTF-8') from ex
        elif not isinstance(host, str):
            raise TypeError(f'{self.name}: expected {host!r} to be of type {bytes} or {str}')
        if not host.strip():
            raise ValueError(f'{self.name}: host {host!r} is empty')

        if not isinstance(port, int):
            raise TypeError(f'{self.name}: expected {port!r} to be of type {int}')
        if not 1 <= port <= 65535:
            raise ValueError(f'{self.name}: port {port!r} is not within 1-65535')

        return f'{host}:{port}'
