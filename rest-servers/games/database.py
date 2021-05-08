#!/usr/bin/env python3


"""
File : database.py

Interface with the sqlite database
"""
import sqlite3
import typing
import pathlib
import unicodedata
import lzma
import base64

# File holding the SQLITE database
FILE = "./db/games.db"

STR_SEPARATOR = ';'
BYTES_SEPARATOR = b';'

STR_SEPARATOR_SUBSTITUTE_FOR_TEXT = ':'
BYTES_SEPARATOR_SUBSTITUTE_FOR_TEXT = b':'

STR_SEPARATOR_SUBSTITUTE_FOR_UNREADABLE = '|'
BYTES_SEPARATOR_SUBSTITUTE_FOR_UNREADABLE = b'|'


def sanitize_field(field_content: str) -> str:
    """ Any str to something that goes into the database """

    assert isinstance(field_content, str), "Sanitize applicable only to strings"
    nfkd_form = unicodedata.normalize('NFKD', field_content)
    only_ascii = nfkd_form.encode('ASCII', 'ignore')
    back_str = only_ascii.decode()
    without_separator = back_str.replace(STR_SEPARATOR, STR_SEPARATOR_SUBSTITUTE_FOR_TEXT)
    return without_separator


def compress_text(text: str) -> str:
    """ compresses text that can be long """
    byte_form = text.encode()
    compressed = lzma.compress(byte_form)
    a85 = base64.a85encode(compressed)
    assert BYTES_SEPARATOR_SUBSTITUTE_FOR_UNREADABLE not in a85
    removed_semicolon = a85.replace(BYTES_SEPARATOR, BYTES_SEPARATOR_SUBSTITUTE_FOR_UNREADABLE)
    return removed_semicolon.decode('ascii')


def uncompress_text(unreadable_str: str) -> str:
    """ uncompresses text that can be long """
    unreadable = unreadable_str.encode('ascii')
    restored_semicolon = unreadable.replace(BYTES_SEPARATOR_SUBSTITUTE_FOR_UNREADABLE, BYTES_SEPARATOR)
    compressed_back = base64.a85decode(restored_semicolon)
    byte_form_back = lzma.decompress(compressed_back)
    text_back = byte_form_back.decode()
    return text_back


def db_remove() -> None:
    """ For testing puprpose"""

    db_file = pathlib.Path(FILE)
    if not db_file.is_file():
        return
    db_file.unlink()


def db_present() -> bool:
    """ Answers the question"""

    db_file = pathlib.Path(FILE)
    return db_file.is_file()


class SqlExecutor:
    """ Object capable of executing sql requests """

    def __init__(self) -> None:
        self._connection = sqlite3.connect(FILE, detect_types=sqlite3.PARSE_DECLTYPES)

    def execute(self, command: str, parameters: typing.Optional[typing.Tuple[typing.Any, ...]] = None, need_result: bool = False) -> typing.Optional[typing.List[typing.Any]]:
        """ Executes a sql command """

        # Note : ignoring Ctrl-C is not possible in flask-rest context

        cursor = self._connection.cursor()
        if parameters:
            cursor.execute(command, parameters)
        else:
            cursor.execute(command)
        result = cursor.fetchall() if need_result else None
        cursor.close()

        return result

    def __del__(self) -> None:
        self._connection.commit()  # necessary otherwise nothing happens
        self._connection.close()


if __name__ == '__main__':
    assert False, "Do not run this script"
