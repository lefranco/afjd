#!/usr/bin/env python3


"""
File : newss.py

Handles the news
"""

import database


class News:
    """ Class for handling a news """

    @staticmethod
    def content(sql_executor: database.SqlExecutor) -> str:
        """ get content """

        content_found = sql_executor.execute("SELECT content FROM newss", None, need_result=True)
        content = content_found[0][0]  # type: ignore
        return content  # type: ignore

    @staticmethod
    def create_table(sql_executor: database.SqlExecutor) -> None:
        """ creation of table from scratch """

        # create actual table
        sql_executor.execute("DROP TABLE IF EXISTS newss")
        sql_executor.execute("CREATE TABLE newss (content str)")
        sql_executor.execute("INSERT INTO newss (content) VALUES (?)", (" ",))

    def __init__(self, content: str) -> None:

        assert isinstance(content, str), "content must be a str"
        self._content = content

    def update_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Pushes changes from object to database """
        sql_executor.execute("DELETE FROM newss")
        sql_executor.execute("INSERT INTO newss (content) VALUES (?)", (self._content,))

    def __str__(self) -> str:
        return f"content={self._content}"


if __name__ == '__main__':
    assert False, "Do not run this script"
