#!/usr/bin/env python3


"""
File : ratings.py

Handles the ratings (ELO) of players
"""
import typing

import database


class Rating:
    """ Class for handling a rating """

    @staticmethod
    def list_by_classic(sql_executor: database.SqlExecutor, classic: bool) -> typing.List[typing.Tuple[int, int, int, int, int, int, int]]:
        """ class lookup : finds the object in database from fame id """
        ratings_found = sql_executor.execute("SELECT * FROM ratings where classic = ?", (int(classic), ), need_result=True)
        if not ratings_found:
            return []
        return ratings_found

    @staticmethod
    def list_by_classic_role_id(sql_executor: database.SqlExecutor, classic: bool, role_id: int) -> typing.List[typing.Tuple[int, int, int, int, int, int, int]]:
        """ class lookup : finds the object in database from fame id """
        ratings_found = sql_executor.execute("SELECT * FROM ratings where classic = ? and role_id = ?", (int(classic), role_id), need_result=True)
        if not ratings_found:
            return []
        return ratings_found

    @staticmethod
    def create_table(sql_executor: database.SqlExecutor) -> None:
        """ creation of table from scratch """

        sql_executor.execute("DROP TABLE IF EXISTS ratings")
        sql_executor.execute("CREATE TABLE ratings (classic INTEGER, role_id INTEGER, player_id INTEGER, elo_value INTEGER, change INTEGER, game_id INTEGER, number_games INTEGER)")

    def __init__(self, classic: bool, role_id: int, player_id: int, elo_value: int, change: int, game_id: int, number_games: int) -> None:

        assert isinstance(classic, bool), "classic must be a bool"
        self._classic = classic

        assert isinstance(role_id, int), "role_id must be an int"
        self._role_id = role_id

        assert isinstance(player_id, int), "player_id must be an int"
        self._player_id = player_id

        assert isinstance(elo_value, int), "elo_value must be an int"
        self._elo_value = elo_value

        assert isinstance(change, int), "change must be an int"
        self._change = change

        assert isinstance(game_id, int), "game_id must be an int"
        self._game_id = game_id

        assert isinstance(number_games, int), "number_games must be an int"
        self._number_games = number_games

    def update_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Pushes changes from object to database """
        sql_executor.execute("INSERT OR REPLACE INTO ratings (classic, role_id, player_id, elo_value, change, game_id, number_games) VALUES (?, ?, ?, ?, ?, ?, ?)", (self._classic, self._role_id, self._player_id, self._elo_value, self._change, self._game_id, self._number_games))

    def delete_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Removes object from database """
        sql_executor.execute("DELETE FROM ratings WHERE classic = ? AND role_id = ? AND player_id = ?", (self._classic, self._role_id, self._player_id))

    def __str__(self) -> str:
        return f"classic={self._classic} role_id={self._role_id} player_id={self._player_id} elo_value={self._elo_value} change={self._change} game_id={self._game_id} number_games={self._number_games}"


if __name__ == '__main__':
    assert False, "Do not run this script"
