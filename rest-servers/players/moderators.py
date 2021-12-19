#!/usr/bin/env python3


"""
File : moderators.py

Handles the moderators
"""

import typing

import database


class Moderator:
    """ Class for handling moderators """

    @staticmethod
    def inventory(sql_executor: database.SqlExecutor) -> typing.List[str]:
        """ class inventory : gives a list of all objects in database """
        moderators_found = sql_executor.execute("SELECT * FROM moderators", need_result=True)
        if not moderators_found:
            return []
        return moderators_found

    @staticmethod
    def create_table(sql_executor: database.SqlExecutor) -> None:
        """ creation of table from scratch """

        # create actual table
        sql_executor.execute("DROP TABLE IF EXISTS moderators")
        sql_executor.execute("CREATE TABLE moderators (pseudo STR UNIQUE PRIMARY KEY)")

    def __init__(self, pseudo: str) -> None:

        assert isinstance(pseudo, str), "pseudo must be a str"
        self._pseudo = pseudo

    def update_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Pushes changes from object to database """
        sql_executor.execute("INSERT OR REPLACE INTO moderators (pseudo) VALUES (?)", (self._pseudo,))

    def delete_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Removes object from database """
        sql_executor.execute("DELETE FROM moderators WHERE pseudo = ?", (self._pseudo,))

    def __str__(self) -> str:
        return f"pseudo={self._pseudo}"


if __name__ == '__main__':
    assert False, "Do not run this script"
