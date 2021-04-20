#!/usr/bin/env python3


"""
File : visits.py

Handles the stored votes
"""
import typing

import database


class Vote:
    """ Class for handling an vote """

    @staticmethod
    def list_by_game_id(game_id: int) -> typing.List[typing.Tuple[int, int, int, int]]:
        """ class lookup : finds the object in database from fame id """
        votes_found = database.sql_execute("SELECT * FROM votes where game_id = ?", (game_id,), need_result=True)
        if not votes_found:
            return []
        return votes_found

    @staticmethod
    def list_by_game_id_role_num(game_id: int, role_num: int) -> typing.List[typing.Tuple[int, int, int, int]]:
        """ class lookup : finds the object in database from fame id """
        votes_found = database.sql_execute("SELECT * FROM votes where game_id = ? and role_num = ?", (game_id, role_num), need_result=True)
        if not votes_found:
            return []
        return votes_found

    @staticmethod
    def create_table() -> None:
        """ creation of table from scratch """

        database.sql_execute("DROP TABLE IF EXISTS votes")
        database.sql_execute("CREATE TABLE votes (game_id INTEGER, role_num INTEGER, vote INTEGER)")

    def __init__(self, game_id: int, role_num: int, vote: bool) -> None:

        assert isinstance(game_id, int), "game_id must be an int"
        self._game_id = game_id

        assert isinstance(role_num, int), "role_num must be an int"
        self._role_num = role_num

        assert isinstance(vote, bool), "role_num must be an bool"
        self._vote = vote

    def update_database(self) -> None:
        """ Pushes changes from object to database """
        database.sql_execute("DELETE FROM votes WHERE game_id = ? and role_num = ?", (self._game_id, self._role_num))
        database.sql_execute("INSERT OR REPLACE INTO votes (game_id, role_num, value) VALUES (?, ?, ?)", (self._game_id, self._role_num, self._vote))

    def delete_database(self) -> None:
        """ Removes object from database """
        database.sql_execute("DELETE FROM votes WHERE game_id = ? AND role_num = ?", (self._game_id, self._role_num))

    def __str__(self) -> str:
        return f"game_id={self._game_id} role_num={self._role_num} vote={self._vote}"


if __name__ == '__main__':
    assert False, "Do not run this script"
