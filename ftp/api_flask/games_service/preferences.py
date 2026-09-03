#!/usr/bin/env python3


"""
File : preferences.py

Handles the stored preferences
"""

import typing

import database


class Preference:
    """ Class for handling a preferences """

    @staticmethod
    def content_by_game_id_player_id(sql_executor: database.SqlExecutor, game_id: int, player_id: int) -> typing.List[typing.Tuple[int, int, str]]:
        """ class lookup : finds the object in database from fame id """
        content_found = sql_executor.execute("SELECT * from preferences where game_id = ? AND player_id = ?", (game_id, player_id), need_result=True)
        if not content_found:
            return []
        return content_found

    @staticmethod
    def content_by_game_id(sql_executor: database.SqlExecutor, game_id: int) -> typing.List[typing.Tuple[int, int, str]]:
        """ class lookup : finds the object in database from fame id """
        content_found = sql_executor.execute("SELECT * from preferences where game_id = ?", (game_id,), need_result=True)
        if not content_found:
            return []
        return content_found

    @staticmethod
    def create_table(sql_executor: database.SqlExecutor) -> None:
        """ creation of table from scratch """

        sql_executor.execute("DROP TABLE IF EXISTS preferences")
        sql_executor.execute("CREATE TABLE preferences (game_id INTEGER, player_id INTEGER, content STR)")

    def __init__(self, game_id: int, player_id: int, content: str) -> None:

        assert isinstance(game_id, int), "game_id must be an int"
        self._game_id = game_id

        assert isinstance(player_id, int), "player_id must be an int"
        self._player_id = player_id

        assert isinstance(content, str), "content must be an str"
        self._content = content

    def update_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Pushes changes from object to database """
        sql_executor.execute("DELETE FROM preferences WHERE game_id = ? and player_id = ?", (self._game_id, self._player_id))
        sql_executor.execute("INSERT OR REPLACE INTO preferences (game_id, player_id, content) VALUES (?, ?, ?)", (self._game_id, self._player_id, self._content))

    def delete_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Removes object from database """
        sql_executor.execute("DELETE FROM preferences WHERE game_id = ? AND player_id = ?", (self._game_id, self._player_id))

    def __str__(self) -> str:
        return f"game_id={self._game_id} player_id={self._player_id} content={self._content}"


if __name__ == '__main__':
    assert False, "Do not run this script"
