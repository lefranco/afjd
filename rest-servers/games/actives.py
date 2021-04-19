#!/usr/bin/env python3


"""
File : actives.py

Handles the active players - that need to enter orders
"""
import typing

import database


class Active:
    """ Class for handling an active """

    @staticmethod
    def list_by_game_id(game_id: int) -> typing.List[typing.Tuple[int, int]]:
        """ class lookup : finds the object in database from fame id """
        actives_found = database.sql_execute("SELECT * FROM actives where game_id = ?", (game_id,), need_result=True)
        if not actives_found:
            return []
        return actives_found

    @staticmethod
    def list_by_game_id_role_num(game_id: int, role_num: int) -> typing.List[typing.Tuple[int, int]]:
        """ class lookup : finds the object in database from fame id """
        actives_found = database.sql_execute("SELECT * FROM actives where game_id = ? and role_num = ?", (game_id, role_num), need_result=True)
        if not actives_found:
            return []
        return actives_found

    @staticmethod
    def create_table() -> None:
        """ creation of table from scratch """

        database.sql_execute("DROP TABLE IF EXISTS actives")
        database.sql_execute("CREATE TABLE actives (game_id INTEGER, role_num INTEGER)")

    def __init__(self, game_id: int, role_num: int) -> None:

        assert isinstance(game_id, int), "game_id must be an int"
        self._game_id = game_id

        assert isinstance(role_num, int), "role_num must be an int"
        self._role_num = role_num

    def update_database(self) -> None:
        """ Pushes changes from object to database """
        database.sql_execute("INSERT OR REPLACE INTO actives (game_id, role_num) VALUES (?, ?)", (self._game_id, self._role_num))

    def delete_database(self) -> None:
        """ Removes object from database """
        database.sql_execute("DELETE FROM actives WHERE game_id = ? AND role_num = ?", (self._game_id, self._role_num))

    def __str__(self) -> str:
        return f"game_id={self._game_id} role_num={self._role_num}"


if __name__ == '__main__':
    assert False, "Do not run this script"
