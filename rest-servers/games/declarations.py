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
    def list_with_content_by_game_id(sql_executor: database.SqlExecutor, game_id: int) -> typing.List[typing.Tuple[int, int, int, int, int, int, contents.Content]]:
        """ class lookup : finds the object in database from fame id """
        declarations_found = sql_executor.execute("SELECT game_id, identifier, author_num, anonymous, announce, time_stamp, content_data FROM declarations INNER JOIN contents ON contents.identifier = declarations.content_id where game_id = ? ORDER BY time_stamp DESC", (game_id,), need_result=True)
        if not declarations_found:
            return []
        return declarations_found

    @staticmethod
    def list_by_game_id(sql_executor: database.SqlExecutor, game_id: int) -> typing.List[typing.Tuple[int, int, int, int, int]]:
        """ class lookup : finds the object in database from fame id """
        declarations_found = sql_executor.execute("SELECT * FROM declarations where game_id = ?", (game_id,), need_result=True)
        if not declarations_found:
            return []
        return declarations_found

    @staticmethod
    def create_table(sql_executor: database.SqlExecutor) -> None:
        """ creation of table from scratch """

        sql_executor.execute("DROP TABLE IF EXISTS declarations")
        sql_executor.execute("CREATE TABLE declarations (game_id INTEGER, author_num INTEGER, anonymous INTEGER, announce INTEGER, content_id INTEGER UNIQUE PRIMARY KEY)")

    def __init__(self, game_id: int, author_num: int, anonymous: bool, announce: bool, content_id: int) -> None:

        self._game_id = game_id
        self._author_num = author_num
        self._anonymous = anonymous
        self._announce = announce
        self._content_id = content_id

    def update_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Pushes changes from object to database """
        sql_executor.execute("INSERT OR REPLACE INTO declarations (game_id, author_num, anonymous, announce, content_id) VALUES (?, ?, ?, ?, ?)", (self._game_id, self._author_num, self._anonymous, self._announce, self._content_id))

    def delete_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Removes object from database """
        sql_executor.execute("DELETE FROM declarations WHERE content_id = ?", (self._content_id,))

    def __str__(self) -> str:
        return f"game_id={self._game_id} author_num={self._author_num} anonymous={self._anonymous} announce={self._announce} content_id={self._content_id}"


if __name__ == '__main__':
    assert False, "Do not run this script"
