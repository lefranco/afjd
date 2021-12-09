""" memoize """

# pylint: disable=pointless-statement, expression-not-assigned


class MemoizeTable:
    """ MemoizeTable :  uses storage to share a dictionary """

    def __init__(self):
        self._data = dict()

    def __contains__(self, key):
        return key in self._data

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value


# using this avoids a server download (costy on slow connections)
VARIANT_CONTENT_MEMOIZE_TABLE = MemoizeTable()

# using this avoids a read from file (costy on slow computers)
PARAMETERS_READ_MEMOIZE_TABLE = MemoizeTable()

# using this avoids an object creation (always costy)
VARIANT_DATA_MEMOIZE_TABLE = MemoizeTable()
