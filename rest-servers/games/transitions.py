#!/usr/bin/env python3


"""
File : transitions.py

Handles the transitions of the game (history)
"""
import typing
import sqlite3

import database


class Transition:
    """ Class for handling a transition """

    @staticmethod
    def find_by_identifier_advancement(sql_executor: database.SqlExecutor, identifier: int, advancement: int) -> typing.Optional['Transition']:
        """ class lookup : finds the object in database from identifier """
        reports_found = sql_executor.execute("SELECT transition_data FROM transitions where game_id = ? and advancement = ?", (identifier, advancement), need_result=True)
        if not reports_found:
            return None
        return reports_found[0][0]  # type: ignore

    @staticmethod
    def inventory(sql_executor: database.SqlExecutor) -> typing.List['Transition']:
        """ class inventory : gives a list of all objects in transitions """
        transitions_found = sql_executor.execute("SELECT transition_data FROM transitions", need_result=True)
        if not transitions_found:
            return []
        transitions_list = [t[0] for t in transitions_found]
        return transitions_list

    @staticmethod
    def create_table(sql_executor: database.SqlExecutor) -> None:
        """ creation of table from scratch """

        sql_executor.execute("DROP TABLE IF EXISTS transitions")
        sql_executor.execute("CREATE TABLE transitions (game_id INTEGER, advancement INTEGER, transition_data transition, PRIMARY KEY(game_id, advancement))")

    def __init__(self, game_id: int, advancement: int, time_stamp: int, situation_json: str, orders_json: str, report_txt: str) -> None:

        assert isinstance(game_id, int), "game_id must be an int"
        self._game_id = game_id

        assert isinstance(advancement, int), "advancement must be an int"
        self._advancement = advancement

        assert isinstance(time_stamp, int), "time_stamp must be an int"
        self._time_stamp = time_stamp

        assert isinstance(situation_json, str), "situation_json must be an str"
        self._situation_json = situation_json

        assert isinstance(orders_json, str), "orders_json must be an str"
        self._orders_json = orders_json

        assert isinstance(report_txt, str), "report_txt must be an str"
        self._report_txt = report_txt

    def update_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Pushes changes from object to database """
        sql_executor.execute("INSERT OR REPLACE INTO transitions (game_id, advancement, transition_data) VALUES (?, ?, ?)", (self._game_id, self._advancement, self))

    def delete_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Removes object from database """
        sql_executor.execute("DELETE FROM transitions WHERE game_id = ? and advancement = ?", (self._game_id, self._advancement))

    @property
    def time_stamp(self) -> int:
        """ property """
        return self._time_stamp

    @property
    def situation_json(self) -> str:
        """ property """
        return self._situation_json

    @property
    def orders_json(self) -> str:
        """ property """
        return self._orders_json

    @property
    def report_txt(self) -> str:
        """ property """
        return self._report_txt

    def __str__(self) -> str:
        return f"game_id={self._game_id} advancement={self._advancement} time_stamp={self._time_stamp} situation_json={self._situation_json} orders_json={self._orders_json} report_txt={self._report_txt}"

    def adapt_transition(self) -> bytes:
        """ To put an object in database """

        compressed_situation_json = database.compress_text(self._situation_json)
        compressed_orders_json = database.compress_text(self._orders_json)
        compressed_report_txt = database.compress_text(self._report_txt)

        return (f"{self._game_id}{database.STR_SEPARATOR}{self._advancement}{database.STR_SEPARATOR}{self._time_stamp}{database.STR_SEPARATOR}{compressed_situation_json}{database.STR_SEPARATOR}{compressed_orders_json}{database.STR_SEPARATOR}{compressed_report_txt}").encode('ascii')


def convert_transition(buffer: bytes) -> Transition:
    """ To extract an object from database """

    tab = buffer.split(database.BYTES_SEPARATOR)
    identifier = int(tab[0].decode())
    advancement = int(tab[1].decode())
    time_stamp = int(tab[2].decode())

    compressed_orders_json = tab[3].decode()
    orders_json = database.uncompress_text(compressed_orders_json)

    compressed_situation_json = tab[4].decode()
    situation_json = database.uncompress_text(compressed_situation_json)

    compressed_report_txt = tab[5].decode()
    report_txt = database.uncompress_text(compressed_report_txt)

    transition = Transition(identifier, advancement, time_stamp, orders_json, situation_json, report_txt)
    return transition


# Interfaces between python and database
sqlite3.register_adapter(Transition, Transition.adapt_transition)
sqlite3.register_converter('transition', convert_transition)


if __name__ == '__main__':
    assert False, "Do not run this script"
