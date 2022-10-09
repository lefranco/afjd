#!/usr/bin/env python3


"""
File : ratings2.py

Handles the ratings (regularity) of players
"""
import typing

import database


class Rating2:
    """ Class for handling a rating """

    @staticmethod
    def list(sql_executor: database.SqlExecutor) -> typing.List[typing.Tuple[int, int, int, int, int]]:
        """ class lookup : finds the object in database from fame id """
        ratings_found = sql_executor.execute("SELECT * FROM ratings2", need_result=True)
        if not ratings_found:
            return []
        return ratings_found

    @staticmethod
    def create_table(sql_executor: database.SqlExecutor) -> None:
        """ creation of table from scratch """

        sql_executor.execute("DROP TABLE IF EXISTS ratings2")
        sql_executor.execute("CREATE TABLE ratings2 (player_id INTEGER, started_playing_days INTEGER, finished_playing_days INTEGER, activity_days INTEGER, number_games INTEGER)")

    def __init__(self, player_id: int, started_playing_days: int, finished_playing_days: int, activity_days: int, number_games: int) -> None:

        assert isinstance(player_id, int), "player_id must be an int"
        self._player_id = player_id

        assert isinstance(started_playing_days, int), "started_playing_days must be an int"
        self._started_playing_days = started_playing_days

        assert isinstance(finished_playing_days, int), "finished_playing_days must be an int"
        self._finished_playing_days = finished_playing_days

        assert isinstance(activity_days, int), "activity_days must be an int"
        self._activity_days = activity_days

        assert isinstance(number_games, int), "number_games must be an int"
        self._number_games = number_games

    def update_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Pushes changes from object to database """
        sql_executor.execute("INSERT OR REPLACE INTO ratings2 (player_id, started_playing_days, finished_playing_days, activity_days, number_games) VALUES (?, ?, ?, ?, ?)", (self._player_id, self._finished_playing_days, self._activity_days, self._activity_days, self._number_games))

    def delete_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Removes object from database """
        sql_executor.execute("DELETE FROM ratings2 WHERE player_id = ?", (self._player_id, ))

    def __str__(self) -> str:
        return f"player_id={self._player_id} started_playing_days={self._started_playing_days} finished_playing_days={self._finished_playing_days} activity_days={self._activity_days} number_games={self._number_games}"


if __name__ == '__main__':
    assert False, "Do not run this script"
