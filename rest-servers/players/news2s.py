#!/usr/bin/env python3


"""
File : news2s.py

Handles the news (moderator)
"""

import database


class News:
    """ Class for handling a news """

    @staticmethod
    def content(sql_executor: database.SqlExecutor) -> str:
        """ get content """

        content_found = sql_executor.execute("SELECT content FROM news2s", None, need_result=True)
        content = content_found[0][0]  # type: ignore
        return content  # type: ignore

    @staticmethod
    def create_table(sql_executor: database.SqlExecutor) -> None:
        """ creation of table from scratch """

        # create actual table
        sql_executor.execute("DROP TABLE IF EXISTS news2s")
        sql_executor.execute("CREATE TABLE news2s (content str)")
        sql_executor.execute("INSERT INTO news2s (content) VALUES (?)", (" ",))

    def __init__(self, content: str) -> None:

        assert isinstance(content, str), "content must be a str"
        self._content = content

    def update_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Pushes changes from object to database """
        sql_executor.execute("DELETE FROM news2s")
        sql_executor.execute("INSERT INTO news2s (content) VALUES (?)", (self._content,))

    def __str__(self) -> str:
        return f"content={self._content}"


if __name__ == '__main__':
    assert False, "Do not run this script"
