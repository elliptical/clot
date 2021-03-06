"""This module implements descriptors to handle torrent fields."""


from datetime import datetime

from .layout import Attr
from .validators import Bounded, Encoded, NonEmpty, Typed, UnixEpoch, ValidUrl, ValidUrlList


class Field(Attr, Typed):
    """Field with specific type and unrestricted values, including None."""

    def __init__(self, key, value_type, **kwargs):
        """Initialize self."""
        super().__init__(key, value_type=value_type, **kwargs)


class Integer(Field, Bounded):
    """Integer field with optional lower and/or upper bounds."""

    def __init__(self, key, **kwargs):
        """Initialize self."""
        super().__init__(key, int, **kwargs)


class Bytes(Field, NonEmpty):
    """Bytes field with non-empty value."""

    def __init__(self, key, **kwargs):
        """Initialize self."""
        super().__init__(key, bytes, **kwargs)


# pylint: disable=too-many-ancestors


class String(Field, Encoded, NonEmpty):
    """String field with nonempty value (stored as bytes)."""

    def __init__(self, key, **kwargs):
        """Initialize self."""
        super().__init__(key, str, **kwargs)


class Timestamp(Field, UnixEpoch, Bounded):
    """Timestamp field with required timezone info."""

    def __init__(self, key, **kwargs):
        """Initialize self."""
        super().__init__(key, datetime, **kwargs)


class Url(Attr, ValidUrl):
    """String field looking like an URL (non-empty scheme and hostname required)."""


class UrlList(Attr, ValidUrlList):
    """List of URLs."""
