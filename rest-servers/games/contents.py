#!/usr/bin/env python3


"""
File : contents.py

Handles the contents of messages and declarations
"""
import sqlite3
import typing

import database


class Content:
    """ Class for handling a content """

    @staticmethod
    def free_identifier(sql_executor: database.SqlExecutor) -> int:
        """ class free identifier : finds an new identifier from database to use for this object """
        highest_identifier_found = sql_executor.execute("SELECT MAX(identifier) AS max_identifier FROM contents", None, need_result=True)
        highest_identifier = highest_identifier_found[0][0]  # type: ignore
        if highest_identifier is None:
            return 1
        return highest_identifier + 1  # type: ignore

    @staticmethod
    def list_by_game_id(sql_executor: database.SqlExecutor, game_id: int) -> typing.List[typing.Tuple[int, int, int, int]]:
        """ class lookup : finds the object in database from fame id """
        contents_found = sql_executor.execute("SELECT * FROM contents where game_id2 = ?", (game_id,), need_result=True)
        if not contents_found:
            return []
        return contents_found

    @staticmethod
    def create_table(sql_executor: database.SqlExecutor) -> None:
        """ creation of table from scratch """

        sql_executor.execute("DROP TABLE IF EXISTS contents")
        sql_executor.execute("CREATE TABLE contents (identifier INTEGER UNIQUE PRIMARY KEY, game_id2 INTEGER, time_stamp INTEGER, content_data content)")

    def __init__(self, identifier: int, game_id: int, time_stamp: int, payload: str) -> None:

        assert isinstance(identifier, int), "identifier must be an int"
        self._identifier = identifier

        assert isinstance(game_id, int), "game_id must be an int"
        self._game_id = game_id

        assert isinstance(time_stamp, int), "time_stamp must be an int"
        self._time_stamp = time_stamp

        assert isinstance(payload, str), "payload must be an str"
        self._payload = payload

    def update_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Pushes changes from object to database """
        sql_executor.execute("INSERT OR REPLACE INTO contents (identifier, game_id2, time_stamp, content_data) VALUES (?, ?, ?, ?)", (self._identifier, self._game_id, self._time_stamp, self))

    def delete_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Removes object from database """
        sql_executor.execute("DELETE FROM contents WHERE identifier = ?", (self._identifier,))

    @property
    def identifier(self) -> int:
        """ property """
        return self._identifier

    @property
    def time_stamp(self) -> int:
        """ property """
        return self._time_stamp

    @property
    def payload(self) -> str:
        """ property """
        return self._payload

    def __str__(self) -> str:
        return f"identifier={self._identifier} game_id={self._game_id} time_stamp={self._time_stamp} payload={self._payload}"

    def adapt_content(self) -> bytes:
        """ To put an object in database """
        compressed_payload = database.compress_text(self._payload)
        return (f"{self._identifier}{database.STR_SEPARATOR}{self._game_id}{database.STR_SEPARATOR}{self._time_stamp}{database.STR_SEPARATOR}{compressed_payload}").encode('ascii')


def convert_content(buffer: bytes) -> Content:
    """ To extract an object from database """

    tab = buffer.split(database.BYTES_SEPARATOR)
    identifier = int(tab[0].decode())
    game_id = int(tab[1].decode())
    time_stamp = int(tab[2].decode())

    compressed_payload = tab[3].decode()
    payload = database.uncompress_text(compressed_payload)

    content = Content(identifier, game_id, time_stamp, payload)
    return content


# Interfaces between python and database
sqlite3.register_adapter(Content, Content.adapt_content)
sqlite3.register_converter('content', convert_content)


if __name__ == '__main__':
    assert False, "Do not run this script"
