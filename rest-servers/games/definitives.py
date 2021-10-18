#!/usr/bin/env python3


"""
File : definitive.py

Handles the stored indication orders are definitive
"""
import typing

import database


class Definitive:
    """ Class for handling an indication """

    @staticmethod
    def list_by_game_id(sql_executor: database.SqlExecutor, game_id: int) -> typing.List[typing.Tuple[int, int, int, int]]:
        """ class lookup : finds the object in database from fame id """
        votes_found = sql_executor.execute("SELECT * FROM definitives where game_id = ?", (game_id,), need_result=True)
        if not votes_found:
            return []
        return votes_found

    @staticmethod
    def list_by_game_id_role_num(sql_executor: database.SqlExecutor, game_id: int, role_num: int) -> typing.List[typing.Tuple[int, int, int, int]]:
        """ class lookup : finds the object in database from fame id """
        votes_found = sql_executor.execute("SELECT * FROM definitives where game_id = ? and role_num = ?", (game_id, role_num), need_result=True)
        if not votes_found:
            return []
        return votes_found

    @staticmethod
    def create_table(sql_executor: database.SqlExecutor) -> None:
        """ creation of table from scratch """

        sql_executor.execute("DROP TABLE IF EXISTS definitives")
        sql_executor.execute("CREATE TABLE definitives (game_id INTEGER, role_num INTEGER, value INTEGER)")

    def __init__(self, game_id: int, role_num: int, definitive: bool) -> None:

        assert isinstance(game_id, int), "game_id must be an int"
        self._game_id = game_id

        assert isinstance(role_num, int), "role_num must be an int"
        self._role_num = role_num

        assert isinstance(definitive, bool), "definitive must be an bool"
        self._definitive = definitive

    def update_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Pushes changes from object to database """
        sql_executor.execute("DELETE FROM definitives WHERE game_id = ? and role_num = ?", (self._game_id, self._role_num))
        sql_executor.execute("INSERT OR REPLACE INTO definitives (game_id, role_num, value) VALUES (?, ?, ?)", (self._game_id, self._role_num, self._definitive))

    def delete_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Removes object from database """
        sql_executor.execute("DELETE FROM definitives WHERE game_id = ? AND role_num = ?", (self._game_id, self._role_num))

    def __str__(self) -> str:
        return f"game_id={self._game_id} role_num={self._role_num} definitive={self._definitive}"


if __name__ == '__main__':
    assert False, "Do not run this script"
