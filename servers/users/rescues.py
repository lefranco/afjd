#!/usr/bin/env python3


"""
File : rescues.py

Handles the rescues (request for email with link to get token to change password)
"""
import typing
import time

import database


class Rescue:
    """ Class for handling a Rescue """

    @staticmethod
    def find_all(sql_executor: database.SqlExecutor) -> typing.List['Rescue']:
        """ class lookup : finds all the object in database  """
        failures_found = sql_executor.execute("SELECT * FROM rescues", need_result=True)
        if not failures_found:
            return []
        return failures_found

    @staticmethod
    def create_table(sql_executor: database.SqlExecutor) -> None:
        """ creation of table from scratch """

        sql_executor.execute("DROP TABLE IF EXISTS rescues")
        sql_executor.execute("CREATE TABLE rescues (user_name STR, ip_address STR, date real)")

    def __init__(self, user_name: str, ip_address: str) -> None:

        assert isinstance(user_name, str), "identifier must be an str"
        self._user_name = user_name

        assert isinstance(ip_address, str), "ip_address must be an str"
        self._ip_address = ip_address

        self._date = time.time()

    def update_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Pushes changes from object to database """
        sql_executor.execute("INSERT OR REPLACE INTO rescues (user_name, ip_address, date) VALUES (?, ?, ?)", (self._user_name, self._ip_address, self._date))

    def delete_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Removes object from database """
        sql_executor.execute("DELETE FROM rescues WHERE user_name = ? and date = ?", (self._user_name, self._date))

    def __str__(self) -> str:
        return f"user_name={self._user_name} ip_address={self._ip_address} date={self._date}"


if __name__ == '__main__':
    assert False, "Do not run this script"
