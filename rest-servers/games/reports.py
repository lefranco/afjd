#!/usr/bin/env python3


"""
File : reports.py

Handles the latest report of the game
"""
import typing
import sqlite3

import database


class Report:
    """ Class for handling a report """

    @staticmethod
    def find_by_identifier(identifier: int) -> typing.Optional['Report']:
        """ class lookup : finds the object in database from identifier """
        reports_found = database.sql_execute("SELECT report_data FROM reports where game_id = ?", (identifier,), need_result=True)
        if not reports_found:
            return None
        return reports_found[0][0]  # type: ignore

    @staticmethod
    def create_table() -> None:
        """ creation of table from scratch """

        database.sql_execute("DROP TABLE IF EXISTS reports")
        database.sql_execute("CREATE TABLE reports (game_id INTEGER UNIQUE PRIMARY KEY, report_data report)")

    def __init__(self, game_id: int, time_stamp: int, content: str) -> None:

        assert isinstance(game_id, int), "game_id must be an int"
        self._game_id = game_id

        assert isinstance(time_stamp, int), "time_stamp must be an int"
        self._time_stamp = time_stamp

        assert isinstance(content, str), "content must be an str"
        self._content = content

    def update_database(self) -> None:
        """ Pushes changes from object to database """
        database.sql_execute("INSERT OR REPLACE INTO reports (game_id, report_data) VALUES (?, ?)", (self._game_id, self))

    def delete_database(self) -> None:
        """ Removes object from database """
        database.sql_execute("DELETE FROM reports WHERE game_id = ?", (self._game_id,))

    @property
    def content(self) -> str:
        """ property """
        return self._content

    def __str__(self) -> str:
        return f"game_id={self._game_id} time_stamp={self._time_stamp} content={self._content}"

    def adapt_report(self) -> bytes:
        """ To put an object in database """
        compressed_content = database.compress_text(self._content)
        return (f"{self._game_id}{database.STR_SEPARATOR}{self._time_stamp}{database.STR_SEPARATOR}{compressed_content}").encode('ascii')


def convert_report(buffer: bytes) -> Report:
    """ To extract an object from database """

    tab = buffer.split(database.BYTES_SEPARATOR)
    identifier = int(tab[0].decode())
    time_stamp = int(tab[1].decode())

    compressed_content = tab[2].decode()
    content = database.uncompress_text(compressed_content)

    report = Report(identifier, time_stamp, content)
    return report


# Interfaces between python and database
sqlite3.register_adapter(Report, Report.adapt_report)
sqlite3.register_converter('report', convert_report)


if __name__ == '__main__':
    assert False, "Do not run this script"
