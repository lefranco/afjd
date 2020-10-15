#!/usr/bin/env python3


"""
File : visits.py

Handles the stored visits
"""
import typing

import database


class Visit:
    """ Class for handling an visit """

    @staticmethod
    def list_by_game_id_role_num(game_id: int, role_num: int) -> typing.List[typing.Tuple[int, int, int]]:
        """ class lookup : finds the object in database from fame id """
        visits_found = database.sql_execute("SELECT * FROM visits where game_id = ? and role_num = ?", (game_id, role_num), need_result=True)
        if not visits_found:
            return []
        return visits_found

    @staticmethod
    def create_table() -> None:
        """ creation of table from scratch """

        database.sql_execute("DROP TABLE IF EXISTS visits")
        database.sql_execute("CREATE TABLE visits (game_id INTEGER, role_num INTEGER, time_stamp INTEGER)")

    def __init__(self, game_id: int, role_num: int, time_stamp: int) -> None:

        assert isinstance(game_id, int), "game_id must be an int"
        self._game_id = game_id

        assert isinstance(role_num, int), "role_num must be an int"
        self._role_num = role_num

        assert isinstance(time_stamp, int), "time_stamp must be an int"
        self._time_stamp = time_stamp

    def update_database(self) -> None:
        """ Pushes changes from object to database """
        database.sql_execute("DELETE FROM visits WHERE game_id = ? AND role_num = ?", (self._game_id, self._role_num))
        database.sql_execute("INSERT OR REPLACE INTO visits (game_id, role_num, time_stamp) VALUES (?, ?, ?)", (self._game_id, self._role_num, self._time_stamp))

    def delete_database(self) -> None:
        """ Removes object from database """
        database.sql_execute("DELETE FROM visits WHERE game_id = ? AND role_num = ?", (self._game_id, self._role_num))

    @property
    def time_stamp(self) -> int:
        """ property """
        return self._time_stamp

    def __str__(self) -> str:
        return f"game_id={self._game_id} role_num={self._role_num} time_stamp={self._time_stamp}"


if __name__ == '__main__':
    assert False, "Do not run this script"
