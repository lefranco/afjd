#!/usr/bin/env python3


"""
File : incidents.py

Handles the players - that have submitted orders late
"""
import typing

import database


class Incident:
    """ Class for handling an incident """

    @staticmethod
    def list_by_game_id(sql_executor: database.SqlExecutor, game_id: int) -> typing.List[typing.Tuple[int, int, int]]:
        """ class lookup : finds the object in database from game id """
        incidents_found = sql_executor.execute("SELECT * FROM incidents where game_id = ?", (game_id,), need_result=True)
        if not incidents_found:
            return []
        return incidents_found

    @staticmethod
    def create_table(sql_executor: database.SqlExecutor) -> None:
        """ creation of table from scratch """

        sql_executor.execute("DROP TABLE IF EXISTS incidents")
        sql_executor.execute("CREATE TABLE incident (game_id INTEGER, role_num INTEGER, advancement INTEGER)")

    def __init__(self, game_id: int, role_num: int, advancement: int) -> None:

        assert isinstance(game_id, int), "game_id must be an int"
        self._game_id = game_id

        assert isinstance(role_num, int), "role_num must be an int"
        self._role_num = role_num

        assert isinstance(advancement, int), "advancement must be an int"
        self._advancement = advancement

    def update_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Pushes changes from object to database """
        sql_executor.execute("DELETE FROM incident WHERE game_id = ? AND role_num = ? AND advancement = ?", (self._game_id, self._role_num, self._advancement))
        sql_executor.execute("INSERT OR REPLACE INTO incident (game_id, role_num, incident) VALUES (?, ?)", (self._game_id, self._role_num, self._advancement))

    def delete_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Removes object from database """
        sql_executor.execute("DELETE FROM incident WHERE game_id = ? AND role_num = ? and incident = ?", (self._game_id, self._role_num, self._advancement))

    def __str__(self) -> str:
        return f"game_id={self._game_id} role_num={self._role_num} incident={self._advancement}"


if __name__ == '__main__':
    assert False, "Do not run this script"
