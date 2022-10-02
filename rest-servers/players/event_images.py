#!/usr/bin/env python3


"""
File : registrations.py

Handles the event images
"""
import typing

import database


class EventImage:
    """ Class for handling a event_image """

    @staticmethod
    def find_by_identifier(sql_executor: database.SqlExecutor, identifier: int) -> typing.Optional[bytes]:
        """ class lookup : finds the object in database from identifier """
        event_images_found = sql_executor.execute("SELECT content FROM event_images where event_id = ?", (identifier,), need_result=True)
        if not event_images_found:
            return None
        return event_images_found[0][0]  # type: ignore

    @staticmethod
    def create_table(sql_executor: database.SqlExecutor) -> None:
        """ creation of table from scratch """

        sql_executor.execute("DROP TABLE IF EXISTS event_images")
        sql_executor.execute("CREATE TABLE event_images (event_id INTEGER, content BLOB)")

    def __init__(self, event_id: int, content: bytes) -> None:

        assert isinstance(event_id, int), "event_id must be an int"
        self._event_id = event_id

        assert isinstance(content, bytes), "content must be an bytes"
        self._content = content

    def update_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Pushes changes from object to database """
        sql_executor.execute("DELETE FROM event_images WHERE event_id = ?", (self._event_id,))
        sql_executor.execute("INSERT OR REPLACE INTO event_images (event_id, content) VALUES (?, ?)", (self._event_id, self._content))

    def delete_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Removes object from database """
        sql_executor.execute("DELETE FROM event_images WHERE event_id = ?", (self._event_id,))

    def __str__(self) -> str:
        return f"event_id={self._event_id} image=xxx"


if __name__ == '__main__':
    assert False, "Do not run this script"
