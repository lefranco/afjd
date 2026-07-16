#!/usr/bin/env python3


"""
File : teasers.py

Handles the teasers
"""

import database


class Teaser:
    """ Class for handling teasers """

    @staticmethod
    def content(sql_executor: database.SqlExecutor, variant: str) -> str:
        """ get content """

        content_found = sql_executor.execute("SELECT content FROM teasers where variant=?", (variant,), need_result=True)
        content = content_found[0][0]  # type: ignore
        return content  # type: ignore

    @staticmethod
    def create_table(sql_executor: database.SqlExecutor) -> None:
        """ creation of table from scratch """

        # create actual table
        sql_executor.execute("DROP TABLE IF EXISTS teasers")

        # teaser
        sql_executor.execute("CREATE TABLE teasers (variant str, content str)")

    def __init__(self, variant: str, content: str) -> None:

        assert isinstance(variant, str), "variant must be a str"
        assert isinstance(content, str), "content must be a str"
        self._variant = variant
        self._content = content

    def update_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Pushes changes from object to database """
        sql_executor.execute("DELETE FROM teasers where variant = ?", (self._variant,))
        sql_executor.execute("INSERT INTO teasers (variant, content) VALUES (?, ?)", (self._variant, self._content))

    def __str__(self) -> str:
        return f"variant={self._variant} content={self._content}"


if __name__ == '__main__':
    assert False, "Do not run this script"
