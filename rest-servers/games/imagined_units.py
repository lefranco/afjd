#!/usr/bin/env python3


"""
File : imagined_units.py

Handles the units of positions
"""
import typing

import database


class ImaginedUnit:
    """ Class for handling a imagined unit """

    @staticmethod
    def list_by_game_id(sql_executor: database.SqlExecutor, game_id: int) -> typing.List[typing.Tuple[int, int, int, int]]:
        """ class lookup : finds the object in database from fame id """
        units_found = sql_executor.execute("SELECT * FROM imagined_units where game_id = ?", (game_id,), need_result=True)
        if not units_found:
            return []
        return units_found

    @staticmethod
    def list_by_game_id_role_num(sql_executor: database.SqlExecutor, game_id: int, role_num: int) -> typing.List[typing.Tuple[int, int, int]]:
        """ class lookup : finds the object in database from fame id """
        units_found = sql_executor.execute("SELECT * FROM imagined_units where game_id = ? and role_num = ?", (game_id, role_num), need_result=True)
        if not units_found:
            return []
        return units_found

    @staticmethod
    def create_table(sql_executor: database.SqlExecutor) -> None:
        """ creation of table from scratch """

        sql_executor.execute("DROP TABLE IF EXISTS imagined_units")
        sql_executor.execute("CREATE TABLE imagined_units (game_id INTEGER, type_num INTEGER, zone_num INTEGER, role_num INTEGER)")

    def __init__(self, game_id: int, type_num: int, zone_num: int, role_num: int) -> None:

        assert isinstance(game_id, int), "game_id must be an int"
        self._game_id = game_id

        assert isinstance(type_num, int), "type_num must be an int"
        self._type_num = type_num

        assert isinstance(zone_num, int), "zone_num must be an int"
        self._zone_num = zone_num

        assert isinstance(role_num, int), "role_num must be an int"
        self._role_num = role_num

    def update_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Pushes changes from object to database """
        sql_executor.execute("INSERT OR REPLACE INTO imagined_units (game_id, type_num, zone_num, role_num) VALUES (?, ?, ?, ?)", (self._game_id, self._type_num, self._zone_num, self._role_num))

    def delete_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Removes object from database """
        sql_executor.execute("DELETE FROM imagined_units WHERE game_id = ? AND zone_num = ?", (self._game_id, self._zone_num))

    def __str__(self) -> str:
        return f"game_id={self._game_id} type_num={self._type_num} zone_num={self._zone_num} role_num={self._role_num}"


if __name__ == '__main__':
    assert False, "Do not run this script"
