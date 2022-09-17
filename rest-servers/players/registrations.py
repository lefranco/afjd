#!/usr/bin/env python3


"""
File : registrations.py

Handles the registrations
"""
import typing

import database


class Registration:
    """ Class for handling a registration """

    @staticmethod
    def list_by_event_id(sql_executor: database.SqlExecutor, event_id: int) -> typing.List[typing.Tuple[int, int]]:
        """ class lookup : finds the object in database from event id """
        registrations_found = sql_executor.execute("SELECT * FROM registrations where event_id = ?", (event_id,), need_result=True)
        if not registrations_found:
            return []
        return registrations_found

    @staticmethod
    def inventory(sql_executor: database.SqlExecutor) -> typing.List[typing.Tuple[int, int, int]]:
        """ class inventory : gives a list of all objects in database """
        registrations_found = sql_executor.execute("SELECT * FROM registrations", need_result=True)
        if not registrations_found:
            return []
        return registrations_found

    @staticmethod
    def create_table(sql_executor: database.SqlExecutor) -> None:
        """ creation of table from scratch """

        sql_executor.execute("DROP TABLE IF EXISTS registrations")
        sql_executor.execute("CREATE TABLE registrations (event_id INTEGER, player_id INTEGER)")

    def __init__(self, event_id: int, player_id: int) -> None:

        assert isinstance(event_id, int), "event_id must be an int"
        self._event_id = event_id

        assert isinstance(player_id, int), "player_id must be an int"
        self._player_id = player_id

    def update_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Pushes changes from object to database """
        sql_executor.execute("INSERT OR REPLACE INTO registrations (event_id, player_id) VALUES (?, ?)", (self._event_id, self._player_id))

    def delete_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Removes object from database """
        sql_executor.execute("DELETE FROM registrations WHERE event_id = ? AND player_id = ?", (self._event_id, self._player_id))

    def __str__(self) -> str:
        return f"event_id={self._event_id} player_id={self._player_id}"


if __name__ == '__main__':
    assert False, "Do not run this script"
