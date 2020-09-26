#!/usr/bin/env python3


"""
File : forbiddens.py

Handles the forbiddens of positions
"""
import typing

import database


class Forbidden:
    """ Class for handling a forbidden """

    @staticmethod
    def list_by_game_id(game_id: int) -> typing.List[typing.Tuple[int, int]]:
        """ class lookup : finds the object in database from fame id """
        forbiddens_found = database.sql_execute("SELECT * FROM forbiddens where game_id = ?", (game_id,), need_result=True)
        if not forbiddens_found:
            return []
        return forbiddens_found

    @staticmethod
    def create_table() -> None:
        """ creation of table from scratch """

        database.sql_execute("DROP TABLE IF EXISTS forbiddens")
        database.sql_execute("CREATE TABLE forbiddens (game_id INTEGER, region_num INTEGER)")

    def __init__(self, game_id: int, region_num: int) -> None:

        assert isinstance(game_id, int), "game_id must be an int"
        self._game_id = game_id

        assert isinstance(region_num, int), "region_num must be an int"
        self._region_num = region_num

    def update_database(self) -> None:
        """ Pushes changes from object to database """
        database.sql_execute("INSERT OR REPLACE INTO forbiddens (game_id, region_num) VALUES (?, ?)", (self._game_id, self._region_num))

    def delete_database(self) -> None:
        """ Removes object from database """
        database.sql_execute("DELETE FROM forbiddens WHERE game_id = ? AND region_num = ?", (self._game_id, self._region_num))

    def __str__(self) -> str:
        return f"game_id={self._game_id} region_num={self._region_num}"


if __name__ == '__main__':
    assert False, "Do not run this script"
