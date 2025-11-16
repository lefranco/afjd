#!/usr/bin/env python3


"""
File : incidents2.py

Handles the players - that had a civil disorder (game master forced their orders)
"""
import typing
import time

import database


class Incident2:
    """ Class for handling an incident2 """

    @staticmethod
    def list_by_game_id(sql_executor: database.SqlExecutor, game_id: int) -> typing.List[typing.Tuple[int, int, int, float]]:
        """ class lookup : finds the object in database from game id """
        incidents_found = sql_executor.execute("SELECT * FROM incidents2 where game_id = ?", (game_id,), need_result=True)
        if not incidents_found:
            return []
        return incidents_found

    @staticmethod
    def create_table(sql_executor: database.SqlExecutor) -> None:
        """ creation of table from scratch """

        sql_executor.execute("DROP TABLE IF EXISTS incidents2")
        sql_executor.execute("CREATE TABLE incidents2 (game_id INTEGER, role_num INTEGER, advancement INTEGER, date real)")

    def __init__(self, game_id: int, role_num: int, advancement: int) -> None:

        assert isinstance(game_id, int), "game_id must be an int"
        self._game_id = game_id

        assert isinstance(role_num, int), "role_num must be an int"
        self._role_num = role_num

        assert isinstance(advancement, int), "advancement must be an int"
        self._advancement = advancement

        self._date = time.time()

    def update_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Pushes changes from object to database """
        sql_executor.execute("DELETE FROM incidents2 WHERE game_id = ? AND role_num = ? AND advancement = ?", (self._game_id, self._role_num, self._advancement))
        sql_executor.execute("INSERT OR REPLACE INTO incidents2 (game_id, role_num, advancement, date) VALUES (?, ?, ?, ?)", (self._game_id, self._role_num, self._advancement, self._date))

    def delete_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Removes object from database """
        sql_executor.execute("DELETE FROM incidents2 WHERE game_id = ? AND role_num = ? and advancement = ?", (self._game_id, self._role_num, self._advancement))

    def __str__(self) -> str:
        return f"game_id={self._game_id} role_num={self._role_num} advancement={self._advancement}  date={self._date}"


if __name__ == '__main__':
    assert False, "Do not run this script"
