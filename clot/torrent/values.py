"""This module implements custom value types."""


from collections.abc import MutableSequence


class List(MutableSequence):    # pylint: disable=too-many-ancestors
    """A list of items satisfiying the constraint passed in."""

    def __init__(self, valid_item, *values):
        """Initialize self."""
        self.valid_item = valid_item
        filtered_values = (value for value in values if value is not None)
        valid_values = (self.valid_item(value) for value in filtered_values)
        self.data = list(value for value in valid_values if value is not None)

    def __repr__(self):
        """Return repr(self)."""
        return f'{type(self).__name__}({self.data})'

    def __len__(self):
        """Return len(self)."""
        return len(self.data)

    def __getitem__(self, index):
        """Return self[index]."""
        return self.data[index]

    def __setitem__(self, index, value):
        """Set self[index] to value."""
        if isinstance(index, slice):
            self.data[index] = list(self.valid_item(item) for item in value)
        else:
            self.data[index] = self.valid_item(value)

    def __delitem__(self, index):
        """Delete self[index]."""
        del self.data[index]

    def insert(self, index, value):
        """Insert value before index."""
        self.data.insert(index, self.valid_item(value))
