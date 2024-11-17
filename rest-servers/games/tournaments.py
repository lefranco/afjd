#!/usr/bin/env python3


"""
File : tournaments.py

Handles the tournaments
"""
import typing
import sqlite3

import database
import groupings
import assignments

# need to have a limit in sizes of fields
LEN_NAME_MAX = 50


class Tournament:
    """ Class for handling a tournament """

    @staticmethod
    def free_identifier(sql_executor: database.SqlExecutor) -> int:
        """ finds an new identifier from database to use for this object """
        sql_executor.execute("UPDATE tournaments_counter SET value = value + 1", None, need_result=False)
        counter_found = sql_executor.execute("SELECT value FROM tournaments_counter", None, need_result=True)
        counter = counter_found[0][0]  # type: ignore
        return counter  # type: ignore

    @staticmethod
    def find_by_identifier(sql_executor: database.SqlExecutor, identifier: int) -> typing.Optional['Tournament']:
        """ class lookup : finds the object in database from identifier """
        tournaments_found = sql_executor.execute("SELECT tournament_data FROM tournaments where identifier = ?", (identifier,), need_result=True)
        if not tournaments_found:
            return None
        return tournaments_found[0][0]  # type: ignore

    @staticmethod
    def find_by_name(sql_executor: database.SqlExecutor, name: str) -> typing.Optional['Tournament']:
        """ class lookup : finds the object in database from name """
        tournaments_found = sql_executor.execute("SELECT tournament_data FROM tournaments where name = ?", (name,), need_result=True)
        if not tournaments_found:
            return None
        return tournaments_found[0][0]  # type: ignore

    @staticmethod
    def inventory(sql_executor: database.SqlExecutor) -> typing.List['Tournament']:
        """ class inventory : gives a list of all objects in database """
        tournaments_found = sql_executor.execute("SELECT tournament_data FROM tournaments", need_result=True)
        if not tournaments_found:
            return []
        tournaments_list = [g[0] for g in tournaments_found]
        return tournaments_list

    @staticmethod
    def create_table(sql_executor: database.SqlExecutor) -> None:
        """ creation of table from scratch """

        # create counter
        sql_executor.execute("DROP TABLE IF EXISTS tournaments_counter")
        sql_executor.execute("CREATE TABLE tournaments_counter (value INTEGER)")
        sql_executor.execute("INSERT INTO tournaments_counter (value) VALUES (?)", (0,))

        # create actual table
        sql_executor.execute("DROP TABLE IF EXISTS tournaments")
        sql_executor.execute("CREATE TABLE tournaments (identifier INTEGER UNIQUE PRIMARY KEY, name STR, tournament_data tournament)")
        sql_executor.execute("CREATE UNIQUE INDEX name_tournament ON tournaments (name)")

    def __init__(self, identifier: int, name: str) -> None:

        assert isinstance(identifier, int), "identifier must be an int"
        self._identifier = identifier

        assert isinstance(name, str), "name must be a str"
        self._name = name

    def put_director(self, sql_executor: database.SqlExecutor, user_id: int) -> None:
        """ put director in tournament """

        tournament_id = self.identifier
        assignment = assignments.Assignment(tournament_id, user_id)
        assignment.update_database(sql_executor)

    def get_director(self, sql_executor: database.SqlExecutor) -> typing.Optional[int]:
        """ retrieves director id in tournament """

        tournament_id = self.identifier
        assignments_list = assignments.Assignment.list_by_tournament_id(sql_executor, tournament_id)
        for _, player_id in assignments_list:
            return player_id
        return None

    def update_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Pushes changes from object to database """
        sql_executor.execute("INSERT OR REPLACE INTO tournaments (identifier, name, tournament_data) VALUES (?, ?, ?)", (self._identifier, self._name, self))

    def delete_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Removes object from database """
        sql_executor.execute("DELETE FROM tournaments WHERE identifier = ?", (self._identifier,))

    def load_json(self, json_dict: typing.Dict[str, typing.Any]) -> bool:
        """ Load from dict - returns True if changed """

        changed = False

        if 'name' in json_dict and json_dict['name'] is not None and json_dict['name'] != self._name:
            self._name = json_dict['name']
            self._name = database.sanitize_field(self._name)
            self._name = self._name[:LEN_NAME_MAX]
            changed = True

        return changed

    def save_json(self) -> typing.Dict[str, typing.Any]:
        """ Save to  dict """

        json_dict = {
            'name': self._name,
        }
        return json_dict

    def delete_assignments(self, sql_executor: database.SqlExecutor) -> None:
        """  delete assignments """

        tournament_id = self.identifier
        assigments_list = assignments.Assignment.list_by_tournament_id(sql_executor, tournament_id)
        for tournament_id, player_id in assigments_list:
            assigment = assignments.Assignment(tournament_id, player_id)
            assigment.delete_database(sql_executor)

    def delete_groupings(self, sql_executor: database.SqlExecutor) -> None:
        """  delete groupings """

        tournament_id = self.identifier
        groupings_list = groupings.Grouping.list_by_tournament_id(sql_executor, tournament_id)
        for tournament_id, game_id in groupings_list:
            grouping = groupings.Grouping(tournament_id, game_id)
            grouping.delete_database(sql_executor)

    @property
    def identifier(self) -> int:
        """ property """
        return self._identifier

    @property
    def name(self) -> str:
        """ property """
        return self._name

    @name.setter
    def name(self, name: str) -> None:
        """ setter """
        self._name = name

    def __str__(self) -> str:
        return f"name={self._name}"

    def adapt_tournament(self) -> bytes:
        """ To put an object in database """
        return (f"{self._identifier}{database.STR_SEPARATOR}{self._name}").encode('ascii')


def convert_tournament(buffer: bytes) -> Tournament:
    """ To extract an object from database """

    tab = buffer.split(database.BYTES_SEPARATOR)
    identifier = int(tab[0].decode())
    name = tab[1].decode()
    tournament = Tournament(identifier, name)
    return tournament


# Interfaces between python and database
sqlite3.register_adapter(Tournament, Tournament.adapt_tournament)
sqlite3.register_converter('tournament', convert_tournament)


if __name__ == '__main__':
    assert False, "Do not run this script"
