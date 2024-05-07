#!/usr/bin/env python3


"""
File : replacements.py

Handles the players + game master - that have been replaced in a game
"""
import typing
import time

import database


class Replacement:
    """ Class for handling an replacement """

    @staticmethod
    def list_by_player_id(sql_executor: database.SqlExecutor, player_id: int) -> typing.List[typing.Tuple[int, int, int, float]]:
        """ class lookup : finds the object in database from game id """
        replacements_found = sql_executor.execute("SELECT * FROM replacements where player_id = ?", (player_id,), need_result=True)
        if not replacements_found:
            return []
        return replacements_found

    @staticmethod
    def list_by_game_id(sql_executor: database.SqlExecutor, game_id: int) -> typing.List[typing.Tuple[int, int, int, float]]:
        """ class lookup : finds the object in database from game id """
        replacements_found = sql_executor.execute("SELECT * FROM replacements where game_id = ?", (game_id,), need_result=True)
        if not replacements_found:
            return []
        return replacements_found

    @staticmethod
    def inventory(sql_executor: database.SqlExecutor) -> typing.List[typing.Tuple[int, int, int, float]]:
        """ class inventory : gives a list of all objects in database """
        replacements_found = sql_executor.execute("SELECT * FROM replacements", need_result=True)
        if not replacements_found:
            return []
        return replacements_found

    @staticmethod
    def create_table(sql_executor: database.SqlExecutor) -> None:
        """ creation of table from scratch """

        sql_executor.execute("DROP TABLE IF EXISTS replacements")
        sql_executor.execute("CREATE TABLE replacements (game_id INTEGER, role_num INTEGER, player_id INTEGER, date real)")

    def __init__(self, game_id: int, role_num: int, player_id: int) -> None:

        assert isinstance(game_id, int), "game_id must be an int"
        self._game_id = game_id

        assert isinstance(role_num, int), "role_num must be an int"
        self._role_num = role_num

        assert isinstance(player_id, int), "player_id must be an int"
        self._player_id = player_id

        self._date = time.time()

    def update_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Pushes changes from object to database """
        sql_executor.execute("DELETE FROM replacements WHERE game_id = ? AND role_num = ? and player_id = ?", (self._game_id, self._role_num, self._player_id))
        sql_executor.execute("INSERT OR REPLACE INTO replacements (game_id, role_num, player_id, date) VALUES (?, ?, ?, ?)", (self._game_id, self._role_num, self._player_id, self._date))

    def delete_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Removes object from database """
        sql_executor.execute("DELETE FROM replacements WHERE game_id = ? AND role_num = ? and player_id = ?", (self._game_id, self._role_num, self._player_id))

    def __str__(self) -> str:
        return f"game_id={self._game_id} role_num={self._role_num} player_id={self._player_id} date={self._date}"


if __name__ == '__main__':
    assert False, "Do not run this script"
