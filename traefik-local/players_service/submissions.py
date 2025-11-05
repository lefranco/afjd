#!/usr/bin/env python3


"""
File : submissions.py

Handles the submissions
"""

import typing
import time

import database


class Submission:
    """ Class for handling a submission """

    @staticmethod
    def delete_by_player_id(sql_executor: database.SqlExecutor, player_id: int) -> None:
        """ deleting a player """
        sql_executor.execute("DELETE FROM submissions where player_id = ?", (player_id,))

    @staticmethod
    def inventory(sql_executor: database.SqlExecutor) -> typing.List[typing.Tuple[str, int]]:
        """ class inventory : gives a list of all objects in database """
        submissions_found = sql_executor.execute("SELECT * FROM submissions", need_result=True)
        if not submissions_found:
            return []
        return submissions_found

    @staticmethod
    def create_table(sql_executor: database.SqlExecutor) -> None:
        """ creation of table from scratch """

        sql_executor.execute("DROP TABLE IF EXISTS submissions_found")
        sql_executor.execute("CREATE TABLE submissions (player_id INTEGER, date real)")

    def __init__(self, player_id: int) -> None:

        self._date = time.time()

        assert isinstance(player_id, int), "player_id must be an int"
        self._player_id = player_id

    def update_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Pushes changes from object to database """
        sql_executor.execute("DELETE FROM submissions where player_id = ?", (self._player_id,))
        sql_executor.execute("INSERT OR REPLACE INTO submissions (player_id, date) VALUES (?, ?)", (self._player_id, self._date))

    def delete_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Removes object from database """
        sql_executor.execute("DELETE FROM submissions WHERE player_id = ? AND date = ?", (self._player_id, self._date))

    def __str__(self) -> str:
        return f"date={self._date} player_id={self._player_id}"


if __name__ == '__main__':
    assert False, "Do not run this script"
