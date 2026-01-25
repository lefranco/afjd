#!/usr/bin/env python3


"""
File : updates.py

Handles if there are updates to the game for player
"""
import typing

import database


class Update:
    """ Class for handling an indication player not ware that games has changed"""

    @staticmethod
    def list_by_player_id(sql_executor: database.SqlExecutor, player_id: int) -> typing.List[typing.Tuple[int, int, int, int]]:
        """ class lookup : finds the object in database from player id """
        updates_found = sql_executor.execute("SELECT * FROM updates where player_id = ?", (player_id,), need_result=True)
        if not updates_found:
            return []
        return updates_found

    @staticmethod
    def list_by_game_id(sql_executor: database.SqlExecutor, game_id: int) -> typing.List[typing.Tuple[int, int, int, int]]:
        """ class lookup : finds the object in database from game id """
        updates_found = sql_executor.execute("SELECT * FROM updates where game_id = ?", (game_id,), need_result=True)
        if not updates_found:
            return []
        return updates_found

    @staticmethod
    def list_by_game_id_role_num(sql_executor: database.SqlExecutor, game_id: int, role_num: int) -> typing.List[typing.Tuple[int, int, int, int]]:
        """ class lookup : finds the object in database from game id and role num"""
        updates_found = sql_executor.execute("SELECT * FROM updates where game_id = ? and role_num = ?", (game_id, role_num), need_result=True)
        if not updates_found:
            return []
        return updates_found

    @staticmethod
    def create_table(sql_executor: database.SqlExecutor) -> None:
        """ creation of table from scratch """

        sql_executor.execute("DROP TABLE IF EXISTS updates")
        sql_executor.execute("CREATE TABLE updates (game_id INTEGER, role_num INTEGER, player_id INTEGER, value INTEGER)")

    def __init__(self, game_id: int, role_num: int, player_id: int, update: int) -> None:

        assert isinstance(game_id, int), "game_id must be an int"
        self._game_id = game_id

        assert isinstance(role_num, int), "role_num must be an int"
        self._role_num = role_num

        assert isinstance(player_id, int), "player_id must be an int"
        self._player_id = player_id

        assert isinstance(update, int), "update must be an int"
        self._update = update

    def update_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Pushes changes from object to database """
        sql_executor.execute("DELETE FROM updates WHERE game_id = ? and role_num = ?", (self._game_id, self._role_num))
        sql_executor.execute("INSERT OR REPLACE INTO updates (game_id, role_num, player_id, value) VALUES (?, ?, ?, ?)", (self._game_id, self._role_num, self._player_id, self._update))

    def delete_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Removes object from database """
        sql_executor.execute("DELETE FROM updates WHERE game_id = ? AND role_num = ?", (self._game_id, self._role_num))

    def __str__(self) -> str:
        return f"game_id={self._game_id} role_num={self._role_num} player_id={self._player_id} update={self._update}"


if __name__ == '__main__':
    assert False, "Do not run this script"
