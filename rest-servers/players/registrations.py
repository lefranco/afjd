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
    def delete_by_player_id(sql_executor: database.SqlExecutor, player_id: int) -> None:
        """ deleting a player """
        sql_executor.execute("DELETE FROM registrations where player_id = ?", (player_id,))

    @staticmethod
    def list_by_event_id(sql_executor: database.SqlExecutor, event_id: int) -> typing.List[typing.Tuple[int, int, int, int, str]]:
        """ class lookup : finds the object in database from event id """
        registrations_found = sql_executor.execute("SELECT * FROM registrations where event_id = ?", (event_id,), need_result=True)
        if not registrations_found:
            return []
        return registrations_found

    @staticmethod
    def find_date_comment_by_event_id_player_id(sql_executor: database.SqlExecutor, event_id: int, player_id: int) -> typing.Optional[typing.Tuple[float, str]]:
        """ class lookup : finds the object in database from identifier """
        registrations_found = sql_executor.execute("SELECT date, comment FROM registrations where event_id = ? and player_id = ?", (event_id, player_id), need_result=True)
        if not registrations_found:
            return None
        return registrations_found[0][0], registrations_found[0][1]

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
        sql_executor.execute("CREATE TABLE registrations (event_id INTEGER, player_id INTEGER, date real, approved INTEGER, comment STR)")

    def __init__(self, event_id: int, player_id: int, date_: float, approved: int, comment: str) -> None:

        assert isinstance(event_id, int), "event_id must be an int"
        self._event_id = event_id

        assert isinstance(player_id, int), "player_id must be an int"
        self._player_id = player_id

        assert isinstance(date_, float), "date must be an float"
        self._date = date_

        assert isinstance(approved, int), "approved must be an int"
        self._approved = approved

        assert isinstance(comment, str), "comment must be a str"
        self._comment = comment

    def update_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Pushes changes from object to database """
        sql_executor.execute("DELETE FROM registrations WHERE event_id = ? AND player_id = ?", (self._event_id, self._player_id))
        sql_executor.execute("INSERT OR REPLACE INTO registrations (event_id, player_id, date, approved, comment) VALUES (?, ?, ?, ?, ?)", (self._event_id, self._player_id, self._date, self._approved, self._comment))

    def delete_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Removes object from database """
        sql_executor.execute("DELETE FROM registrations WHERE event_id = ? AND player_id = ?", (self._event_id, self._player_id))

    def __str__(self) -> str:
        return f"event_id={self._event_id} player_id={self._player_id} date={self._date} approved={self._approved} comment={self._comment}"


if __name__ == '__main__':
    assert False, "Do not run this script"
