#!/usr/bin/env python3


"""
File : registrations.py

Handles the site image
"""

import database


class SiteImage:
    """ Class for handling a site image """

    @staticmethod
    def content(sql_executor: database.SqlExecutor) -> bytes:
        """ get content """

        content_found = sql_executor.execute("SELECT content FROM site_image", None, need_result=True)
        import sys
        print(f"{content_found=}", file=sys.stderr)
        content = content_found[0][0]  # type: ignore
        return content  # type: ignore

    @staticmethod
    def create_table(sql_executor: database.SqlExecutor) -> None:
        """ creation of table from scratch """

        sql_executor.execute("DROP TABLE IF EXISTS site_image")
        sql_executor.execute("CREATE TABLE site_image (content BLOB)")
        sql_executor.execute("INSERT INTO site_image (content) VALUES (?)", (" ",))

    def __init__(self, content: bytes) -> None:

        assert isinstance(content, bytes), "content must be an bytes"
        self._content = content

    def update_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Pushes changes from object to database """
        sql_executor.execute("DELETE FROM site_image")
        sql_executor.execute("INSERT OR REPLACE INTO site_image (content) VALUES (?)", (self._content,))

    def delete_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Removes object from database """
        sql_executor.execute("DELETE FROM site_image ")

    def __str__(self) -> str:
        return f"image={self._content[0:5]!r}"


if __name__ == '__main__':
    assert False, "Do not run this script"
