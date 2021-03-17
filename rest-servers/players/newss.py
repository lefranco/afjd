#!/usr/bin/env python3


"""
File : newss.py

Handles the news
"""
import typing
import sqlite3

import database


class News:
    """ Class for handling a news """

    @staticmethod
    def content() -> str:
        """ get content """

        content_found = database.sql_execute("SELECT content FROM newss", None, need_result=True)
        content = content_found[0][0]  # type: ignore
        return content  # type: ignore

    @staticmethod
    def create_table() -> None:
        """ creation of table from scratch """

        # create actual table
        database.sql_execute("DROP TABLE IF EXISTS newss")
        database.sql_execute("CREATE TABLE newss (content str)")
        database.sql_execute("INSERT INTO newss (content) VALUES (?)", (" ",))

    def __init__(self, content: str) -> None:

        assert isinstance(content, str), "content must be a str"
        self._content = content

    def update_database(self) -> None:
        """ Pushes changes from object to database """
        database.sql_execute("DELETE FROM newss")
        database.sql_execute("INSERT INTO newss (content) VALUES (?)", (self._content,))

    def __str__(self) -> str:
        return f"content={self._content}"


if __name__ == '__main__':
    assert False, "Do not run this script"
