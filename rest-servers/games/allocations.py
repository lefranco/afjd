#!/usr/bin/env python3


"""
File : games.py

Handles the allocations
"""
import typing

import database


class Allocation:
    """ Class for handling a allocation """

    @staticmethod
    def list_by_player_id(player_id: int) -> typing.List[typing.Tuple[int, int, int]]:
        """ class lookup : finds the object in database from fame id """
        allocations_found = database.sql_execute("SELECT * FROM allocations where player_id = ?", (player_id,), need_result=True)
        if not allocations_found:
            return []
        return allocations_found

    @staticmethod
    def list_by_game_id(game_id: int) -> typing.List[typing.Tuple[int, int, int]]:
        """ class lookup : finds the object in database from fame id """
        allocations_found = database.sql_execute("SELECT * FROM allocations where game_id = ?", (game_id,), need_result=True)
        if not allocations_found:
            return []
        return allocations_found

    @staticmethod
    def inventory() -> typing.List['Allocation']:
        """ class inventory : gives a list of all objects in database """
        allocations_found = database.sql_execute("SELECT * FROM allocations", need_result=True)
        if not allocations_found:
            return []
        allocations_list = [a for a in allocations_found]
        return allocations_list

    @staticmethod
    def create_table() -> None:
        """ creation of table from scratch """

        database.sql_execute("DROP TABLE IF EXISTS allocations")
        database.sql_execute("CREATE TABLE allocations (game_id INTEGER, player_id INTEGER, role_id INTEGER)")

    def __init__(self, game_id: int, player_id: int, role_id: int) -> None:

        assert isinstance(game_id, int), "game_id must be an int"
        self._game_id = game_id

        assert isinstance(player_id, int), "player_id must be an int"
        self._player_id = player_id

        assert isinstance(role_id, int), "role_id must be an int"
        self._role_id = role_id

    def update_database(self) -> None:
        """ Pushes changes from object to database """
        database.sql_execute("DELETE FROM allocations WHERE game_id = ? AND player_id = ?", (self._game_id, self._player_id))
        database.sql_execute("INSERT OR REPLACE INTO allocations (game_id, player_id, role_id) VALUES (?, ?, ?)", (self._game_id, self._player_id, self._role_id))

    def delete_database(self) -> None:
        """ Removes object from database """
        database.sql_execute("DELETE FROM allocations WHERE game_id = ? AND player_id = ?", (self._game_id, self._player_id))

    def __str__(self) -> str:
        return f"game_id={self._game_id} player_id={self._player_id} role_id={self._role_id}"


if __name__ == '__main__':
    assert False, "Do not run this script"
