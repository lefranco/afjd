#!/usr/bin/env python3


"""
File : games.py

Handles the units of positions
"""
import typing

import database


class Unit:
    """ Class for handling a unit """

    @staticmethod
    def list_by_game_id(game_id: int) -> typing.List[typing.Tuple[int, int, int, int, int, int]]:
        """ class lookup : finds the object in database from fame id """
        units_found = database.sql_execute("SELECT * FROM units where game_id = ?", (game_id,), need_result=True)
        if not units_found:
            return []
        return units_found

    @staticmethod
    def list_by_game_id_role_num(game_id: int, role_num: int) -> typing.List[typing.Tuple[int, int, int, int, int, int]]:
        """ class lookup : finds the object in database from fame id """
        units_found = database.sql_execute("SELECT * FROM units where game_id = ? and role_num = ?", (game_id, role_num), need_result=True)
        if not units_found:
            return []
        return units_found

    @staticmethod
    def create_table() -> None:
        """ creation of table from scratch """

        database.sql_execute("DROP TABLE IF EXISTS units")
        database.sql_execute("CREATE TABLE units (game_id INTEGER, type_num INTEGER, zone_num INTEGER, role_num INTEGER, region_dislodged_from_num INTEGER, fake INTEGER)")

    def __init__(self, game_id: int, type_num: int, zone_num: int, role_num: int, region_dislodged_from_num: int, fake: int) -> None:

        assert isinstance(game_id, int), "game_id must be an int"
        self._game_id = game_id

        assert isinstance(type_num, int), "type_num must be an int"
        self._type_num = type_num

        assert isinstance(zone_num, int), "zone_num must be an int"
        self._zone_num = zone_num

        assert isinstance(role_num, int), "role_num must be an int"
        self._role_num = role_num

        # 0 for normal unit - not retreating
        assert isinstance(region_dislodged_from_num, int), "region_dislodged_from_num must be an int"
        self._region_dislodged_from_num = region_dislodged_from_num

        # 0 for normal unit - not planning to be built
        assert isinstance(fake, int), "fake must be an int"
        self._fake = fake

    def update_database(self) -> None:
        """ Pushes changes from object to database """
        database.sql_execute("INSERT OR REPLACE INTO units (game_id, type_num, zone_num, role_num, region_dislodged_from_num, fake) VALUES (?, ?, ?, ?, ?, ?)", (self._game_id, self._type_num, self._zone_num, self._role_num, self._region_dislodged_from_num, self._fake))

    def delete_database(self) -> None:
        """ Removes object from database """
        database.sql_execute("DELETE FROM units WHERE game_id = ? AND zone_num = ?", (self._game_id, self._zone_num))

    def __str__(self) -> str:
        return f"game_id={self._game_id} type_num={self._type_num} zone_num={self._zone_num} role_num={self._role_num} region_dislodged_from_num={self._region_dislodged_from_num} fake={self._fake}"


if __name__ == '__main__':
    assert False, "Do not run this script"
