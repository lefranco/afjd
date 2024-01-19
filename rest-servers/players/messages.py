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
    def addressee_by_message_id(sql_executor: database.SqlExecutor, message_id: int) -> int:
        """ class lookup : finds the object in database from message_id """
        messages_found = sql_executor.execute("SELECT addressee_num FROM messages WHERE content_id = ?", (message_id,), need_result=True)
        return messages_found[0][0]  # type: ignore

    @staticmethod
    def list_with_content_by_player_id(sql_executor: database.SqlExecutor, player_id: int) -> typing.List[typing.Tuple[int, int, int, int, contents.Content]]:
        """ class lookup : finds the object in database from fame id """
        messages_found = sql_executor.execute("SELECT identifier, author_num, addressee_num, time_stamp, content_data FROM messages INNER JOIN contents ON contents.identifier = messages.content_id WHERE ? in (author_num, addressee_num) ORDER BY time_stamp DESC", (player_id,), need_result=True)
        if not messages_found:
            return []
        return messages_found

    @staticmethod
    def create_table(sql_executor: database.SqlExecutor) -> None:
        """ creation of table from scratch """

        sql_executor.execute("DROP TABLE IF EXISTS messages")
        sql_executor.execute("CREATE TABLE messages (author_num INT, addressee_num INT, content_id INTEGER)")

    def __init__(self, author_num: int, addressee_num: int, content_id: int) -> None:

        self._author_num = author_num
        self._addressee_num = addressee_num
        self._content_id = content_id

    def update_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Pushes changes from object to database """
        sql_executor.execute("INSERT OR REPLACE INTO messages (author_num, addressee_num, content_id) VALUES (?, ?, ?)", (self._author_num, self._addressee_num, self._content_id))

    def delete_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Removes object from database """
        sql_executor.execute("DELETE FROM messages WHERE content_id = ?", (self._content_id,))

    def __str__(self) -> str:
        return f"author_num={self._author_num} addressee_num={self._addressee_num} content_id={self._content_id}"


if __name__ == '__main__':
    assert False, "Do not run this script"
