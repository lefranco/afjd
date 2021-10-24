#!/usr/bin/env python3


"""
File : logins.py

Handles the logins
"""
import typing
import sqlite3
import time

import database


class Login:
    """ Class for handling a Login """

    @staticmethod
    def find_all(sql_executor: database.SqlExecutor) -> typing.Optional['Login']:
        """ class lookup : finds all the object in database  """
        logins_found = sql_executor.execute("SELECT * FROM logins", need_result=True)
        if not logins_found:
            return []
        return logins_found  # type: ignore

    @staticmethod
    def create_table(sql_executor: database.SqlExecutor) -> None:
        """ creation of table from scratch """

        sql_executor.execute("DROP TABLE IF EXISTS logins")
        sql_executor.execute("CREATE TABLE logins (user_name STR UNIQUE PRIMARY KEY, date real)")

    def __init__(self, user_name: str) -> None:

        assert isinstance(user_name, str), "identifier must be an str"
        self._user_name = user_name

        self._date = time.time()

    def update_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Pushes changes from object to database """
        sql_executor.execute("INSERT OR REPLACE INTO logins (user_name, date) VALUES (?, ?)", (self._user_name, self._date))

    def delete_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Removes object from database """
        sql_executor.execute("DELETE FROM logins WHERE user_name = ?", (self._user_name,))

    def __str__(self) -> str:
        return f"user_name={self._user_name} date={self._date}"


if __name__ == '__main__':
    assert False, "Do not run this script"
