""" memoize """

# pylint: disable=pointless-statement, expression-not-assigned

#  from browser.local_storage import storage  # pylint: disable=import-error


class MemoizeTable:
    """ MemoizeTable :  uses storage to share a dictionary """

    def __init__(self):
        self._data = dict()

    def keys(self):
        """ the keys() method of a dict """
        return self._data.keys()

    def __contains__(self, key):
        return key in self._data

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value

    def __delitem__(self, key):
        del self._data[key]


VARIANT_DATA_MEMOIZE_TABLE = MemoizeTable()
PARAMETERS_READ_MEMOIZE_TABLE = MemoizeTable()
VARIANT_CONTENT_MEMOIZE_TABLE = MemoizeTable()
