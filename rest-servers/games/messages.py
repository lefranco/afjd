#!/usr/bin/env python3


"""
File : messages.py

Handles the messages
"""
import sqlite3
import typing

import database


class Message:
    """ Class for handling a message """

    @staticmethod
    def free_identifier() -> int:
        """ class free identifier : finds an new identifier from database to use for this object """
        highest_identifier_found = database.sql_execute("SELECT MAX(identifier) AS max_identifier FROM messages", None, need_result=True)
        highest_identifier = highest_identifier_found[0][0]  # type: ignore
        if highest_identifier is None:
            return 1
        return highest_identifier + 1  # type: ignore

    @staticmethod
    def list_by_game_id(game_id: int) -> typing.List[typing.Tuple[int, int, 'Message']]:
        """ class lookup : finds the object in database from fame id """
        messages_found = database.sql_execute("SELECT * FROM messages where game_id = ?", (game_id,), need_result=True)
        if not messages_found:
            return []
        return messages_found

    @staticmethod
    def create_table() -> None:
        """ creation of table from scratch """

        database.sql_execute("DROP TABLE IF EXISTS messages")
        database.sql_execute("CREATE TABLE messages (identifier INT UNIQUE PRIMARY KEY, game_id INT, message_data message)")

    def __init__(self, identifier: int, game_id: int, time_stamp: int, author_num: int, addressee_num: int, content: str) -> None:

        assert isinstance(identifier, int), "identifier must be an int"
        self._identifier = identifier

        self._game_id = game_id
        self._time_stamp = time_stamp
        self._author_num = author_num
        self._addressee_num = addressee_num
        self._content = content

    def export(self) -> typing.Tuple[int, int, int, int, str]:
        """ for passing to solver """
        return self._game_id, self._time_stamp, self._author_num, self._addressee_num, self._content

    def update_database(self) -> None:
        """ Pushes changes from object to database """
        database.sql_execute("INSERT OR REPLACE INTO messages (identifier, game_id, message_data) VALUES (?, ?, ?)", (self._identifier, self._game_id, self))

    def delete_database(self) -> None:
        """ Removes object from database """
        database.sql_execute("DELETE FROM messages WHERE identifier = ?", (self._identifier,))

    @property
    def identifier(self) -> int:
        """ property """
        return self._identifier

    @property
    def time_stamp(self) -> int:
        """ property """
        return self._time_stamp

    @property
    def author_num(self) -> int:
        """ property """
        return self._author_num

    @property
    def addressee_num(self) -> int:
        """ property """
        return self._addressee_num

    def __str__(self) -> str:
        return f"identifier={self._identifier}  game_id={self._game_id} time_stamp={self._time_stamp} author_num={self._author_num} addressee_num={self._addressee_num} content={self._content}"

    def adapt_message(self) -> bytes:
        """ To put an object in database """
        compressed_content = database.compress_text(self._content)
        return (f"{self._identifier}{database.STR_SEPARATOR}{self._game_id}{database.STR_SEPARATOR}{self._time_stamp}{database.STR_SEPARATOR}{self._author_num}{database.STR_SEPARATOR}{self._addressee_num}{database.STR_SEPARATOR}{compressed_content}").encode('ascii')


def convert_message(buffer: bytes) -> Message:
    """ To extract an object from database """

    tab = buffer.split(database.BYTES_SEPARATOR)
    identifier = int(tab[0].decode())
    game_id = int(tab[1].decode())
    time_stamp = int(tab[2].decode())
    author_num = int(tab[3].decode())
    addressee_num = int(tab[4].decode())

    compressed_content = tab[5].decode()
    content = database.uncompress_text(compressed_content)

    message = Message(identifier, game_id, time_stamp, author_num, addressee_num, content)
    return message


# Interfaces between python and database
sqlite3.register_adapter(Message, Message.adapt_message)
sqlite3.register_converter('message', convert_message)


if __name__ == '__main__':
    assert False, "Do not run this script"
