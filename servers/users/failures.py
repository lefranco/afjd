#!/usr/bin/env python3


"""
File : failures.py

Handles the failures (failed logins)
"""
import typing
import time

import database


class Failure:
    """ Class for handling a Failure """

    @staticmethod
    def find_all(sql_executor: database.SqlExecutor) -> typing.List['Failure']:
        """ class lookup : finds all the object in database  """
        failures_found = sql_executor.execute("SELECT * FROM failures", need_result=True)
        if not failures_found:
            return []
        return failures_found

    @staticmethod
    def create_table(sql_executor: database.SqlExecutor) -> None:
        """ creation of table from scratch """

        sql_executor.execute("DROP TABLE IF EXISTS failures")
        sql_executor.execute("CREATE TABLE failures (user_name STR, date real)")

    def __init__(self, user_name: str) -> None:

        assert isinstance(user_name, str), "identifier must be an str"
        self._user_name = user_name

        self._date = time.time()

    def update_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Pushes changes from object to database """
        sql_executor.execute("INSERT OR REPLACE INTO failures (user_name, date) VALUES (?, ?)", (self._user_name, self._date))

    def delete_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Removes object from database """
        sql_executor.execute("DELETE FROM failures WHERE user_name = ? and date = ?", (self._user_name, self._date))

    def __str__(self) -> str:
        return f"user_name={self._user_name} date={self._date}"


if __name__ == '__main__':
    assert False, "Do not run this script"
