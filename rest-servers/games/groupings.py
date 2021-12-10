#!/usr/bin/env python3


"""
File : groupings.py

Handles the groupings
"""
import typing

import database


class Grouping:
    """ Class for handling a grouping """

    @staticmethod
    def list_by_game_id(sql_executor: database.SqlExecutor, player_id: int) -> typing.List[typing.Tuple[int, int]]:
        """ class lookup : finds the object in database from game id """
        groupings_found = sql_executor.execute("SELECT * FROM groupings where game_id = ?", (player_id,), need_result=True)
        if not groupings_found:
            return []
        return groupings_found

    @staticmethod
    def list_by_tournament_id(sql_executor: database.SqlExecutor, game_id: int) -> typing.List[typing.Tuple[int, int]]:
        """ class lookup : finds the object in database from tournament id """
        groupings_found = sql_executor.execute("SELECT * FROM groupings where tournament_id = ?", (game_id,), need_result=True)
        if not groupings_found:
            return []
        return groupings_found

    @staticmethod
    def inventory(sql_executor: database.SqlExecutor) -> typing.List[typing.Tuple[int, int, int]]:
        """ class inventory : gives a list of all objects in database """
        groupings_found = sql_executor.execute("SELECT * FROM groupings", need_result=True)
        if not groupings_found:
            return []
        return groupings_found

    @staticmethod
    def create_table(sql_executor: database.SqlExecutor) -> None:
        """ creation of table from scratch """

        sql_executor.execute("DROP TABLE IF EXISTS groupings")
        sql_executor.execute("CREATE TABLE groupings (tournament_id INTEGER, game_id INTEGER)")

    def __init__(self, tournament_id: int, game_id: int) -> None:

        assert isinstance(tournament_id, int), "tournament_id must be an int"
        self._tournament_id = tournament_id

        assert isinstance(game_id, int), "game_id must be an int"
        self._game_id = game_id

    def update_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Pushes changes from object to database """
        sql_executor.execute("INSERT OR REPLACE INTO groupings (tournament_id, game_id) VALUES (?, ?)", (self._tournament_id, self._game_id))

    def delete_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Removes object from database """
        sql_executor.execute("DELETE FROM groupings WHERE tournament_id = ? AND game_id = ?", (self._tournament_id, self._game_id))

    def __str__(self) -> str:
        return f"tournament_id={self._tournament_id} game_id={self._game_id}"


if __name__ == '__main__':
    assert False, "Do not run this script"
