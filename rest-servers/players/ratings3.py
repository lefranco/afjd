#!/usr/bin/env python3


"""
File : ratings3.py

Handles the ratings (reliability) of players
"""
import typing

import database


class Rating3:
    """ Class for handling a rating """

    @staticmethod
    def list(sql_executor: database.SqlExecutor) -> typing.List[typing.Tuple[int, int, int, int]]:
        """ class lookup : finds the object in database from fame id """
        ratings_found = sql_executor.execute("SELECT * FROM ratings3", need_result=True)
        if not ratings_found:
            return []
        return ratings_found

    @staticmethod
    def create_table(sql_executor: database.SqlExecutor) -> None:
        """ creation of table from scratch """

        sql_executor.execute("DROP TABLE IF EXISTS ratings3")
        sql_executor.execute("CREATE TABLE ratings3 (player_id INTEGER, number_delays INTEGER, number_dropouts INTEGER, number_advancements INTEGER)")

    def __init__(self, player_id: int, number_delays: int, number_dropouts: int, number_advancements: int) -> None:

        assert isinstance(player_id, int), "player_id must be an int"
        self._player_id = player_id

        assert isinstance(number_delays, int), "number_delays must be an int"
        self._number_delays = number_delays

        assert isinstance(number_dropouts, int), "number_dropouts must be an int"
        self._number_dropouts = number_dropouts

        assert isinstance(number_advancements, int), "number_advancements must be an int"
        self._number_advancements = number_advancements

    def update_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Pushes changes from object to database """
        sql_executor.execute("INSERT OR REPLACE INTO ratings3 (player_id, number_delays, number_dropouts, number_advancements) VALUES (?, ?, ?, ?)", (self._player_id, self._number_delays, self._number_dropouts, self._number_advancements))

    def delete_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Removes object from database """
        sql_executor.execute("DELETE FROM ratings3 WHERE player_id = ?", (self._player_id, ))

    def __str__(self) -> str:
        return f"player_id={self._player_id} number_delays={self._number_delays} number_dropouts={self._number_dropouts} number_advancements={self._number_advancements}"


if __name__ == '__main__':
    assert False, "Do not run this script"
