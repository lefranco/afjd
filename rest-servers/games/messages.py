#!/usr/bin/env python3


"""
File : messages.py

Handles the messages
"""
import typing

import contents
import database


class Message:
    """ Class for handling a message """

    @staticmethod
    def list_with_content_by_game_id(game_id: int) -> typing.List[typing.Tuple[int, int, int, int, contents.Content]]:
        """ class lookup : finds the object in database from fame id """
        messages_found = database.sql_execute("SELECT game_id, author_num, addressee_num, time_stamp, content_data FROM messages INNER JOIN contents ON contents.identifier = messages.content_id where game_id = ? ORDER BY time_stamp DESC", (game_id,), need_result=True)
        if not messages_found:
            return []
        return messages_found

    @staticmethod
    def create_table() -> None:
        """ creation of table from scratch """

        database.sql_execute("DROP TABLE IF EXISTS messages")
        database.sql_execute("CREATE TABLE messages (game_id INT, author_num INT, addressee_num INT, content_id INT UNIQUE PRIMARY KEY)")

    def __init__(self, game_id: int, author_num: int, addressee_num: int, content_id: int) -> None:

        self._game_id = game_id
        self._author_num = author_num
        self._addressee_num = addressee_num
        self._content_id = content_id

    def update_database(self) -> None:
        """ Pushes changes from object to database """
        database.sql_execute("INSERT OR REPLACE INTO messages (game_id, author_num, addressee_num, content_id) VALUES (?, ?, ?, ?)", (self._game_id, self._author_num, self._addressee_num, self._content_id))

    def delete_database(self) -> None:
        """ Removes object from database """
        database.sql_execute("DELETE FROM messages WHERE content_id = ?", (self._content_id,))

    def __str__(self) -> str:
        return f"game_id={self._game_id} author_num={self._author_num} addressee_num={self._addressee_num} content_id={self._content_id}"


if __name__ == '__main__':
    assert False, "Do not run this script"
