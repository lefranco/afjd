#!/usr/bin/env python3


"""
File : capacities.py

Handles the number of expected players of the game
"""
import typing
import sqlite3

import database


class Capacity:
    """ Class for handling a capacity """

    @staticmethod
    def find_by_identifier(sql_executor: database.SqlExecutor, identifier: int) -> typing.Optional['Report']:
        """ class lookup : finds the object in database from identifier """
        capacities_found = sql_executor.execute("SELECT * FROM capacities where game_id = ?", (identifier,), need_result=True)
        if not capacities_found:
            return None
        return rcapacities_found[0][0]  # type: ignore

    @staticmethod
    def create_table(sql_executor: database.SqlExecutor) -> None:
        """ creation of table from scratch """

        sql_executor.execute("DROP TABLE IF EXISTS capacities")
        sql_executor.execute("CREATE TABLE capacities (game_id INTEGER UNIQUE PRIMARY KEY, value INTEGER)")

    def __init__(self, game_id: int, value: int) -> None:

        assert isinstance(game_id, int), "game_id must be an int"
        self._game_id = game_id

        assert isinstance(value, int), "time_stamp must be an int"
        self._value = value


    def update_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Pushes changes from object to database """
        sql_executor.execute("INSERT OR REPLACE INTO capacities (game_id, value) VALUES (?, ?)", (self._game_id, self._value))

    def delete_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Removes object from database """
        sql_executor.execute("DELETE FROM capacities WHERE game_id = ?", (self._game_id,))

    @property
    def value(self) -> int:
        """ property """
        return self._value

    def __str__(self) -> str:
        return f"game_id={self._game_id} value={self._value}"


if __name__ == '__main__':
    assert False, "Do not run this script"
