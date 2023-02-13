#!/usr/bin/env python3


"""
File : newss.py

Handles the news
"""

import database


class News:
    """ Class for handling a news """

    @staticmethod
    def content(sql_executor: database.SqlExecutor, topic: str) -> str:
        """ get content """

        content_found = sql_executor.execute("SELECT content FROM newss where topic=?", (topic,), need_result=True)
        content = content_found[0][0]  # type: ignore
        return content  # type: ignore

    @staticmethod
    def create_table(sql_executor: database.SqlExecutor) -> None:
        """ creation of table from scratch """

        # create actual table
        sql_executor.execute("DROP TABLE IF EXISTS newss")
        sql_executor.execute("CREATE TABLE newss (topic str, content str)")
        sql_executor.execute("INSERT INTO newss (topic, content) VALUES (?, ?)", ("admin", " "))
        sql_executor.execute("INSERT INTO newss (topic, content) VALUES (?, ?)", ("modo", " "))
        sql_executor.execute("INSERT INTO newss (topic, content) VALUES (?, ?)", ("glory", " "))

    def __init__(self, topic: str, content: str) -> None:

        assert isinstance(topic, str), "topic must be a str"
        assert isinstance(content, str), "content must be a str"
        self._topic = topic
        self._content = content

    def update_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Pushes changes from object to database """
        sql_executor.execute("DELETE FROM newss where topic = ?", (self._topic,))
        sql_executor.execute("INSERT INTO newss (topic, content) VALUES (?, ?)", (self._topic, self._content))

    def __str__(self) -> str:
        return f"topic={self._topic} content={self._content}"


if __name__ == '__main__':
    assert False, "Do not run this script"
