#!/usr/bin/env python3


"""
File : newss.py

Handles the teaser
"""

import database


class Teaser:
    """ Class for handling a teaser """

    @staticmethod
    def content(sql_executor: database.SqlExecutor) -> str:
        """ get content """

        content_found = sql_executor.execute("SELECT content FROM teasers", None, need_result=True)
        content = content_found[0][0]  # type: ignore
        return content  # type: ignore

    @staticmethod
    def create_table(sql_executor: database.SqlExecutor) -> None:
        """ creation of table from scratch """

        # create actual table
        sql_executor.execute("DROP TABLE IF EXISTS teasers")
        sql_executor.execute("CREATE TABLE teasers (content str)")
        sql_executor.execute("INSERT INTO teasers (content) VALUES (?)", (" ",))

    def __init__(self, content: str) -> None:

        assert isinstance(content, str), "content must be a str"
        self._content = content

    def update_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Pushes changes from object to database """
        sql_executor.execute("DELETE FROM teasers")
        sql_executor.execute("INSERT INTO teasers (content) VALUES (?)", (self._content,))

    def __str__(self) -> str:
        return f"content={self._content}"


if __name__ == '__main__':
    assert False, "Do not run this script"
