#!/usr/bin/env python3


"""
File : addresses.py

Handles the addresses (ip addresses)
"""
import typing

import database


class Address:
    """ Class for handling an address """

    @staticmethod
    def inventory(sql_executor: database.SqlExecutor) -> typing.List[typing.Tuple[str, int]]:
        """ class inventory : gives a list of all objects in database """
        addresses_found = sql_executor.execute("SELECT * FROM addresses", need_result=True)
        if not addresses_found:
            return []
        return addresses_found

    @staticmethod
    def create_table(sql_executor: database.SqlExecutor) -> None:
        """ creation of table from scratch """

        sql_executor.execute("DROP TABLE IF EXISTS addresses")
        sql_executor.execute("CREATE TABLE addresses (ip_value STR, player_id INTEGER)")

    def __init__(self, ip_value: str, player_id: int) -> None:

        assert isinstance(ip_value, str), "ip_value must be an str"
        self._ip_value = ip_value

        assert isinstance(player_id, int), "player_id must be an int"
        self._player_id = player_id

    def update_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Pushes changes from object to database """
        sql_executor.execute("DELETE FROM addresses WHERE ip_value = ? AND player_id = ?", (self._ip_value, self._player_id))
        sql_executor.execute("INSERT OR REPLACE INTO addresses (ip_value, player_id) VALUES (?, ?)", (self._ip_value, self._player_id))

    def delete_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Removes object from database """
        sql_executor.execute("DELETE FROM addresses WHERE ip_value = ? AND player_id = ?", (self._ip_value, self._player_id))

    def __str__(self) -> str:
        return f"ip_value={self._ip_value} player_id={self._player_id}"


if __name__ == '__main__':
    assert False, "Do not run this script"
