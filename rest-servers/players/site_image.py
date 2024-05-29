#!/usr/bin/env python3


"""
File : registrations.py

Handles the site image
"""

import typing

import database


class SiteImage:
    """ Class for handling a site image """

    @staticmethod
    def content(sql_executor: database.SqlExecutor) -> typing.Tuple[str, bytes]:
        """ get content """

        item_found = sql_executor.execute("SELECT * FROM site_image", None, need_result=True)
        item = item_found[0]  # type: ignore
        return item  # type: ignore

    @staticmethod
    def create_table(sql_executor: database.SqlExecutor) -> None:
        """ creation of table from scratch """

        sql_executor.execute("DROP TABLE IF EXISTS site_image")
        sql_executor.execute("CREATE TABLE site_image (legend STR, content BLOB)")
        sql_executor.execute("INSERT INTO site_image (legend, content) VALUES (?, ?)", (" ", " "))

    def __init__(self, legend: str, content: bytes) -> None:

        assert isinstance(legend, str), "legend must be a str"
        self._legend = legend

        assert isinstance(content, bytes), "content must be an bytes"
        self._content = content

    def update_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Pushes changes from object to database """
        sql_executor.execute("DELETE FROM site_image")
        sql_executor.execute("INSERT OR REPLACE INTO site_image (legend, content) VALUES (?, ?)", (self._legend, self._content))

    def delete_database(self, sql_executor: database.SqlExecutor) -> None:  # pylint: disable=R0201
        """ Removes object from database """
        sql_executor.execute("DELETE FROM site_image ")

    def __str__(self) -> str:
        return f"legend={self._legend} image={self._content[0:5]!r}"


if __name__ == '__main__':
    assert False, "Do not run this script"
