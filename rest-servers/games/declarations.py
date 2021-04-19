#!/usr/bin/env python3


"""
File : declarations.py

Handles the declarations
"""
import typing

import contents
import database


class Declaration:
    """ Class for handling a declaration """

    @staticmethod
    def list_with_content_by_game_id(game_id: int) -> typing.List[typing.Tuple[int, int, int, int, contents.Content]]:
        """ class lookup : finds the object in database from fame id """
        declarations_found = database.sql_execute("SELECT game_id, author_num, anonymous, time_stamp, content_data FROM declarations INNER JOIN contents ON contents.identifier = declarations.content_id where game_id = ? ORDER BY time_stamp DESC", (game_id,), need_result=True)
        if not declarations_found:
            return []
        return declarations_found

    @staticmethod
    def list_by_game_id(game_id: int) -> typing.List[typing.Tuple[int, int, int, int]]:
        """ class lookup : finds the object in database from fame id """
        declarations_found = database.sql_execute("SELECT * FROM declarations where game_id = ?", (game_id,), need_result=True)
        if not declarations_found:
            return []
        return declarations_found

    @staticmethod
    def create_table() -> None:
        """ creation of table from scratch """

        database.sql_execute("DROP TABLE IF EXISTS declarations")
        database.sql_execute("CREATE TABLE declarations (game_id INT, author_num INT, anonymous INT, content_id INT UNIQUE PRIMARY KEY)")

    def __init__(self, game_id: int, author_num: int, anonymous: bool, content_id: int) -> None:

        self._game_id = game_id
        self._author_num = author_num
        self._anonymous = anonymous
        self._content_id = content_id

    def update_database(self) -> None:
        """ Pushes changes from object to database """
        database.sql_execute("INSERT OR REPLACE INTO declarations (game_id, author_num, anonymous, content_id) VALUES (?, ?, ?)", (self._game_id, self._author_num, self._anonymous, self._content_id))

    def delete_database(self) -> None:
        """ Removes object from database """
        database.sql_execute("DELETE FROM declarations WHERE content_id = ?", (self._content_id,))

    def __str__(self) -> str:
        return f"game_id={self._game_id} author_num={self._author_num} anonymous={self._anonymous} content_id={self._content_id}"


if __name__ == '__main__':
    assert False, "Do not run this script"
