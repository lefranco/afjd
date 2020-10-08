#!/usr/bin/env python3


"""
File : games.py

Handles the declarations
"""
import sqlite3
import typing

import database

# need to have a limit in sizes of fields
LEN_NAME_MAX = 20


class Declaration:
    """ Class for handling a declaration """

    @staticmethod
    def free_identifier() -> int:
        """ class free identifier : finds an new identifier from database to use for this object """
        highest_identifier_found = database.sql_execute("SELECT MAX(identifier) AS max_identifier FROM declarations", None, need_result=True)
        highest_identifier = highest_identifier_found[0][0]  # type: ignore
        if highest_identifier is None:
            return 1
        return highest_identifier + 1  # type: ignore

    @staticmethod
    def list_by_game_id(game_id: int) -> typing.List[typing.Tuple[int, int, 'Declaration']]:
        """ class lookup : finds the object in database from fame id """
        declarations_found = database.sql_execute("SELECT * FROM declarations where game_id = ?", (game_id,), need_result=True)
        if not declarations_found:
            return []
        return declarations_found

    @staticmethod
    def create_table() -> None:
        """ creation of table from scratch """

        database.sql_execute("DROP TABLE IF EXISTS declarations")
        database.sql_execute("CREATE TABLE declarations (identifier INT UNIQUE PRIMARY KEY, game_id INT, declaration_data declaration)")

    def __init__(self, identifier: int, game_id: int, time_stamp: int, author_num: int, content: str) -> None:

        assert isinstance(identifier, int), "identifier must be an int"
        self._identifier = identifier

        self._game_id = game_id
        self._time_stamp = time_stamp
        self._author_num = author_num
        self._content = content

    def export(self) -> typing.Tuple[int, int, int, str]:
        """ for passing to solver """
        return self._game_id, self._time_stamp, self._author_num, self._content

    def update_database(self) -> None:
        """ Pushes changes from object to database """
        database.sql_execute("INSERT OR REPLACE INTO declarations (identifier, game_id, declaration_data) VALUES (?, ?, ?)", (self._identifier, self._game_id, self))

    def delete_database(self) -> None:
        """ Removes object from database """
        database.sql_execute("DELETE FROM declarations WHERE identifier = ?", (self._identifier,))

    @property
    def identifier(self) -> int:
        """ property """
        return self._identifier

    @property
    def time_stamp(self) -> int:
        """ property """
        return self._time_stamp

    def __str__(self) -> str:
        return f"identifier={self._identifier}  game_id={self._game_id} time_stamp={self._time_stamp} author_num={self._author_num} content={self._content}"

    def adapt_declaration(self) -> bytes:
        """ To put an object in database """
        compressed_content = database.compress_text(self._content)
        return (f"{self._identifier}{database.STR_SEPARATOR}{self._game_id}{database.STR_SEPARATOR}{self._time_stamp}{database.STR_SEPARATOR}{self._author_num}{database.STR_SEPARATOR}{compressed_content}").encode('ascii')


def convert_declaration(buffer: bytes) -> Declaration:
    """ To extract an object from database """

    tab = buffer.split(database.BYTES_SEPARATOR)
    identifier = int(tab[0].decode())
    game_id = int(tab[1].decode())
    time_stamp = int(tab[2].decode())
    author_num = int(tab[3].decode())

    compressed_content = tab[4].decode()
    content = database.uncompress_text(compressed_content)

    declaration = Declaration(identifier, game_id, time_stamp, author_num, content)
    return declaration


# Interfaces between python and database
sqlite3.register_adapter(Declaration, Declaration.adapt_declaration)
sqlite3.register_converter('declaration', convert_declaration)


if __name__ == '__main__':
    assert False, "Do not run this script"
