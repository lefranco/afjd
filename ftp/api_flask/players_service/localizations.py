#!/usr/bin/env python3


"""
File : localizations.py

Handles the localizations
"""
import typing

import database


class Localization:
    """ Class for handling a localizations """

    @staticmethod
    def delete_by_player_id(sql_executor: database.SqlExecutor, player_id: int) -> None:
        """ deleting a player """
        sql_executor.execute("DELETE FROM localizations where player_id = ?", (player_id,))

    @staticmethod
    def inventory(sql_executor: database.SqlExecutor) -> typing.List[typing.Tuple[str, int]]:
        """ class inventory : gives a list of all objects in database """
        localizations_found = sql_executor.execute("SELECT * FROM localizations", need_result=True)
        if not localizations_found:
            return []
        return localizations_found

    @staticmethod
    def create_table(sql_executor: database.SqlExecutor) -> None:
        """ creation of table from scratch """

        sql_executor.execute("DROP TABLE IF EXISTS localizations")
        sql_executor.execute("CREATE TABLE localizations (player_id INTEGER, localization_value STR)")

    def __init__(self, player_id: int, localization_value: str) -> None:

        assert isinstance(player_id, int), "player_id must be an int"
        self._player_id = player_id

        assert isinstance(localization_value, str), "localization_value must be an str"
        self._localization_value = localization_value

    def update_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Pushes changes from object to database """
        sql_executor.execute("DELETE FROM localizations WHERE player_id = ?", (self._player_id,))
        sql_executor.execute("INSERT OR REPLACE INTO localizations (player_id, localization_value) VALUES (?, ?)", (self._player_id, self._localization_value))

    def delete_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Removes object from database """
        sql_executor.execute("DELETE FROM localizations WHERE player_id = ?", (self._player_id,))

    def __str__(self) -> str:
        return f"player_id={self._player_id} localization_value={self._localization_value}"


if __name__ == '__main__':
    assert False, "Do not run this script"
