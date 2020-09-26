#!/usr/bin/env python3


"""
File : games.py

Handles the ownerships of positions
"""
import typing

import database


class Ownership:
    """ Class for handling an ownership """

    @staticmethod
    def list_by_game_id(game_id: int) -> typing.List[typing.Tuple[int, int, int]]:
        """ class lookup : finds the object in database from fame id """
        ownerships_found = database.sql_execute("SELECT * FROM ownerships where game_id = ?", (game_id,), need_result=True)
        if not ownerships_found:
            return []
        return ownerships_found

    @staticmethod
    def create_table() -> None:
        """ creation of table from scratch """

        database.sql_execute("DROP TABLE IF EXISTS ownerships")
        database.sql_execute("CREATE TABLE ownerships (game_id INTEGER, center_num INTEGER, role_num INTEGER)")

    def __init__(self, game_id: int, center_num: int, role_num: int) -> None:

        assert isinstance(game_id, int), "game_id must be an int"
        self._game_id = game_id

        assert isinstance(center_num, int), "center_num must be an int"
        self._center_num = center_num

        assert isinstance(role_num, int), "role_num must be an int"
        self._role_num = role_num

    def update_database(self) -> None:
        """ Pushes changes from object to database """
        database.sql_execute("INSERT OR REPLACE INTO ownerships (game_id, center_num, role_num) VALUES (?, ?, ?)", (self._game_id, self._center_num, self._role_num))

    def delete_database(self) -> None:
        """ Removes object from database """
        database.sql_execute("DELETE FROM ownerships WHERE game_id = ? AND center_num = ? AND role_num = ?", (self._game_id, self._center_num, self._role_num))

    def __str__(self) -> str:
        return f"game_id={self._game_id} center_num={self._center_num} role_num={self._role_num}"


if __name__ == '__main__':
    assert False, "Do not run this script"
