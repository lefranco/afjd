#!/usr/bin/env python3


"""
File : assignments.py

Handles the assignments (player as director of tournament)
"""
import typing

import database


class Assignment:
    """ Class for handling a assignment """

    @staticmethod
    def list_by_player_id(sql_executor: database.SqlExecutor, player_id: int) -> typing.List[typing.Tuple[int, int]]:
        """ class lookup : finds the object in database from fame id """
        assignments_found = sql_executor.execute("SELECT * FROM assignments where player_id = ?", (player_id,), need_result=True)
        if not assignments_found:
            return []
        return assignments_found

    @staticmethod
    def list_by_tournament_id(sql_executor: database.SqlExecutor, tournament_id: int) -> typing.List[typing.Tuple[int, int]]:
        """ class lookup : finds the object in database from fame id """
        assignments_found = sql_executor.execute("SELECT * FROM assignments where tournament_id = ?", (tournament_id,), need_result=True)
        if not assignments_found:
            return []
        return assignments_found

    @staticmethod
    def inventory(sql_executor: database.SqlExecutor) -> typing.List[typing.Tuple[int, int, int]]:
        """ class inventory : gives a list of all objects in database """
        assignments_found = sql_executor.execute("SELECT * FROM assignments", need_result=True)
        if not assignments_found:
            return []
        return assignments_found

    @staticmethod
    def create_table(sql_executor: database.SqlExecutor) -> None:
        """ creation of table from scratch """

        sql_executor.execute("DROP TABLE IF EXISTS assignments")
        sql_executor.execute("CREATE TABLE assignments (tournament_id INTEGER, player_id INTEGER)")

    def __init__(self, tournament_id: int, player_id: int) -> None:

        assert isinstance(tournament_id, int), "tournament_id must be an int"
        self._tournament_id = tournament_id

        assert isinstance(player_id, int), "player_id must be an int"
        self._player_id = player_id

    def update_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Pushes changes from object to database """
        sql_executor.execute("DELETE FROM assignments WHERE tournament_id = ?", (self._tournament_id,))
        sql_executor.execute("INSERT INTO assignments (tournament_id, player_id) VALUES (?, ?)", (self._tournament_id, self._player_id))

    def delete_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Removes object from database """
        sql_executor.execute("DELETE FROM assignments WHERE tournament_id = ? AND player_id = ?", (self._tournament_id, self._player_id))

    def __str__(self) -> str:
        return f"tournament_id={self._tournament_id} player_id={self._player_id}"


if __name__ == '__main__':
    assert False, "Do not run this script"
