#!/usr/bin/env python3


"""
File : players.py

Handles the players
"""
import typing
import sqlite3
import pathlib
import json

import database

# need to have a limit in sizes of fields
LEN_PSEUDO_MAX = 20
LEN_EMAIL_MAX = 100
LEN_FAMILY_NAME_MAX = 30
LEN_FIRST_NAME_MAX = 20
LEN_COUNTRY_MAX = 5
LEN_TIMEZONE_MAX = 10

LOCATION = './data'
EXTENSION = '.json'


def check_country(country: str) -> bool:
    """ check country is ok """

    name = "country_list"
    full_name_file = pathlib.Path(LOCATION, name).with_suffix(EXTENSION)
    assert full_name_file.exists(), "Missing file to check countries"
    with open(full_name_file, 'r', encoding="utf-8") as file_ptr:
        json_data = json.load(file_ptr)
    assert isinstance(json_data, dict), "File to check countries is not a dict"
    return country in json_data.values()


def default_country() -> str:
    """ default_country """

    name = "country_list"
    full_name_file = pathlib.Path(LOCATION, name).with_suffix(EXTENSION)
    assert full_name_file.exists(), "Missing file to check countries"
    with open(full_name_file, 'r', encoding="utf-8") as file_ptr:
        json_data = json.load(file_ptr)
    assert isinstance(json_data, dict), "File to check countries is not a dict"
    return str(list(json_data.values())[0])


def check_timezone(timezone: str) -> bool:
    """ check timezone is ok """

    name = "timezone_list"
    full_name_file = pathlib.Path(LOCATION, name).with_suffix(EXTENSION)
    assert full_name_file.exists(), "Missing file to check timezones"
    with open(full_name_file, 'r', encoding="utf-8") as file_ptr:
        json_data = json.load(file_ptr)
    assert isinstance(json_data, dict), "File to check timezones is not a dict"
    return timezone in json_data.values()


def default_timezone() -> str:
    """ default_timezone """

    name = "timezone_list"
    full_name_file = pathlib.Path(LOCATION, name).with_suffix(EXTENSION)
    assert full_name_file.exists(), "Missing file to check timezones"
    with open(full_name_file, 'r', encoding="utf-8") as file_ptr:
        json_data = json.load(file_ptr)
    assert isinstance(json_data, dict), "File to check timezones is not a dict"
    return str(list(json_data.values())[0])


class Player:
    """ Class for handling a player """

    @staticmethod
    def free_identifier(sql_executor: database.SqlExecutor) -> int:
        """ class free identifier : finds an new identifier from database to use for this object """
        sql_executor.execute("UPDATE players_counter SET value = value + 1", None, need_result=True)
        counter_found = sql_executor.execute("SELECT value FROM players_counter", None, need_result=True)
        counter = counter_found[0][0]  # type: ignore
        return counter  # type: ignore

    @staticmethod
    def find_by_identifier(sql_executor: database.SqlExecutor, identifier: int) -> typing.Optional['Player']:
        """ class lookup : finds the object in database from identifier """
        players_found = sql_executor.execute("SELECT player_data FROM players where identifier = ?", (identifier,), need_result=True)
        if not players_found:
            return None
        return players_found[0][0]  # type: ignore

    @staticmethod
    def find_by_pseudo(sql_executor: database.SqlExecutor, pseudo: str) -> typing.Optional['Player']:
        """ class lookup : finds the object in database from pseudo """
        players_found = sql_executor.execute("SELECT player_data FROM players where pseudo = ?", (pseudo,), need_result=True)
        if not players_found:
            return None
        return players_found[0][0]  # type: ignore

    @staticmethod
    def find_by_similar_pseudo(sql_executor: database.SqlExecutor, pseudo: str) -> typing.Optional['Player']:
        """ class lookup : finds the object in database from pseudo """
        players_found = sql_executor.execute("SELECT player_data FROM players where pseudo = ? COLLATE NOCASE", (pseudo,), need_result=True)
        if not players_found:
            return None
        return players_found[0][0]  # type: ignore

    @staticmethod
    def find_admin_pseudo(sql_executor: database.SqlExecutor) -> typing.Optional[str]:
        """ class lookup : finds the first pseudo in database """
        pseudo_found = sql_executor.execute("SELECT pseudo FROM players where identifier = ?", (1,), need_result=True)
        if not pseudo_found:
            return None
        return pseudo_found[0][0]  # type: ignore

    @staticmethod
    def inventory(sql_executor: database.SqlExecutor) -> typing.List['Player']:
        """ class inventory : gives a list of all objects in database """
        players_found = sql_executor.execute("SELECT player_data FROM players", need_result=True)
        if not players_found:
            return []
        players_list = [p[0] for p in players_found]
        return players_list

    @staticmethod
    def create_table(sql_executor: database.SqlExecutor) -> None:
        """ creation of table from scratch """

        # create counter
        sql_executor.execute("DROP TABLE IF EXISTS players_counter")
        sql_executor.execute("CREATE TABLE players_counter (value INT)")
        sql_executor.execute("INSERT INTO players_counter (value) VALUES (?)", (0,))

        # create actual table
        sql_executor.execute("DROP TABLE IF EXISTS players")
        sql_executor.execute("CREATE TABLE players (identifier INT UNIQUE PRIMARY KEY, pseudo STR, player_data player)")
        sql_executor.execute("CREATE UNIQUE INDEX pseudo_player ON  players (pseudo)")

    def __init__(self, identifier: int, pseudo: str, email: str, email_confirmed: bool, notify_deadline: bool, notify_adjudication: bool, notify_message: bool, notify_replace: bool, newsletter: bool, family_name: str, first_name: str, residence: str, nationality: str, time_zone: str) -> None:

        assert isinstance(identifier, int), "identifier must be an int"
        self._identifier = identifier

        assert isinstance(pseudo, str), "pseudo must be a str"
        self._pseudo = pseudo

        self._email = email
        self._email_confirmed = email_confirmed
        self._notify_deadline = notify_deadline
        self._notify_adjudication = notify_adjudication
        self._notify_message = notify_message
        self._notify_replace = notify_replace
        self._newsletter = newsletter
        self._first_name = first_name
        self._family_name = family_name
        self._residence = residence
        self._nationality = nationality
        self._time_zone = time_zone

    def update_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Pushes changes from object to database """
        sql_executor.execute("INSERT OR REPLACE INTO players (identifier, pseudo, player_data) VALUES (?, ?, ?)", (self._identifier, self._pseudo, self))

    def delete_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Removes object from database """
        sql_executor.execute("DELETE FROM players WHERE identifier = ?", (self._identifier,))

    def load_json(self, json_dict: typing.Dict[str, typing.Any]) -> bool:
        """ Load from dict - returns True if changed """

        changed = False

        if 'pseudo' in json_dict and json_dict['pseudo'] is not None and json_dict['pseudo'] != self._pseudo:
            self._pseudo = json_dict['pseudo']
            self._pseudo = database.sanitize_field(self._pseudo)
            self._pseudo = self._pseudo[:LEN_PSEUDO_MAX]
            changed = True

        if 'email' in json_dict and json_dict['email'] is not None and json_dict['email'] != self._email:
            self._email = json_dict['email']
            self._email = database.sanitize_field(self._email)
            self._email = self._email[:LEN_EMAIL_MAX]
            changed = True

        # email_confirmed cannot be set directly

        if 'notify_deadline' in json_dict and json_dict['notify_deadline'] is not None and json_dict['notify_deadline'] != self._notify_deadline:
            self._notify_deadline = json_dict['notify_deadline']
            changed = True

        if 'notify_adjudication' in json_dict and json_dict['notify_adjudication'] is not None and json_dict['notify_adjudication'] != self._notify_adjudication:
            self._notify_adjudication = json_dict['notify_adjudication']
            changed = True

        if 'notify_message' in json_dict and json_dict['notify_message'] is not None and json_dict['notify_message'] != self._notify_message:
            self._notify_message = json_dict['notify_message']
            changed = True

        if 'notify_replace' in json_dict and json_dict['notify_replace'] is not None and json_dict['notify_replace'] != self._notify_replace:
            self._notify_replace = json_dict['notify_replace']
            changed = True

        if 'newsletter' in json_dict and json_dict['newsletter'] is not None and json_dict['newsletter'] != self._newsletter:
            self._newsletter = json_dict['newsletter']
            changed = True

        if 'family_name' in json_dict and json_dict['family_name'] is not None and json_dict['family_name'] != self._family_name:
            self._family_name = json_dict['family_name']
            self._family_name = database.sanitize_field(self._family_name)
            self._family_name = self._family_name[:LEN_FAMILY_NAME_MAX]
            changed = True

        if 'first_name' in json_dict and json_dict['first_name'] is not None and json_dict['first_name'] != self._first_name:
            self._first_name = json_dict['first_name']
            self._first_name = database.sanitize_field(self._first_name)
            self._first_name = self._first_name[:LEN_FIRST_NAME_MAX]
            changed = True

        if 'residence' in json_dict and json_dict['residence'] is not None and json_dict['residence'] != self._residence:
            self._residence = json_dict['residence']
            self._residence = database.sanitize_field(self._residence)
            self._residence = self._residence[:LEN_COUNTRY_MAX]
            changed = True

        if 'nationality' in json_dict and json_dict['nationality'] is not None and json_dict['nationality'] != self._nationality:
            self._nationality = json_dict['nationality']
            self._nationality = database.sanitize_field(self._nationality)
            self._nationality = self._nationality[:LEN_COUNTRY_MAX]
            changed = True

        if 'time_zone' in json_dict and json_dict['time_zone'] is not None and json_dict['time_zone'] != self._time_zone:
            self._time_zone = json_dict['time_zone']
            self._time_zone = database.sanitize_field(self._time_zone)
            self._time_zone = self._time_zone[:LEN_TIMEZONE_MAX]
            changed = True

        return changed

    def save_json(self) -> typing.Dict[str, typing.Any]:
        """ Save to  dict """

        json_dict = {
            'pseudo': self._pseudo,
            'email': self._email,
            'email_confirmed': self._email_confirmed,
            'notify_deadline': self._notify_deadline,
            'notify_adjudication': self._notify_adjudication,
            'notify_message': self._notify_message,
            'notify_replace': self._notify_replace,
            'newsletter': self._newsletter,
            'family_name': self._family_name,
            'first_name': self._first_name,
            'residence': self._residence,
            'nationality': self._nationality,
            'time_zone': self._time_zone,
        }
        return json_dict

    @property
    def identifier(self) -> int:
        """ property """
        return self._identifier

    @property
    def pseudo(self) -> str:
        """ property """
        return self._pseudo

    @property
    def family_name(self) -> str:
        """ property """
        return self._family_name

    @property
    def first_name(self) -> str:
        """ property """
        return self._first_name

    @property
    def residence(self) -> str:
        """ property """
        return self._residence

    @property
    def nationality(self) -> str:
        """ property """
        return self._nationality

    @property
    def time_zone(self) -> str:
        """ property """
        return self._time_zone

    @property
    def email(self) -> str:
        """ property """
        return self._email

    @property
    def email_confirmed(self) -> bool:
        """ property """
        return self._email_confirmed

    @email_confirmed.setter
    def email_confirmed(self, email_confirmed: bool) -> None:
        """ setter """
        self._email_confirmed = email_confirmed

    @property
    def notify_deadline(self) -> bool:
        """ property """
        return self._notify_deadline

    @property
    def notify_adjudication(self) -> bool:
        """ property """
        return self._notify_adjudication

    @property
    def notify_message(self) -> bool:
        """ property """
        return self._notify_message

    @property
    def notify_replace(self) -> bool:
        """ property """
        return self._notify_replace

    @property
    def newsletter(self) -> bool:
        """ property """
        return self._newsletter

    @newsletter.setter
    def newsletter(self, newsletter: bool) -> None:
        """ setter """
        self._newsletter = newsletter

    def __str__(self) -> str:
        return f"pseudo={self._pseudo} email={self._email} email_confirmed={self._email_confirmed} notify_deadline={self._notify_deadline} notify_adjudication={self._notify_adjudication} notify_message={self._notify_message} notify_replace={self._notify_replace} newsletter={self._newsletter} family_name={self._family_name} first_name={self._first_name} residence={self._residence} nationality={self._nationality} time_zone={self._time_zone}"

    def adapt_player(self) -> bytes:
        """ To put an object in database """
        return (f"{self._identifier}{database.STR_SEPARATOR}{self._pseudo}{database.STR_SEPARATOR}{self._email}{database.STR_SEPARATOR}{int(bool(self._email_confirmed))}{database.STR_SEPARATOR}{int(bool(self._notify_deadline))}{database.STR_SEPARATOR}{int(bool(self._notify_adjudication))}{database.STR_SEPARATOR}{int(bool(self._notify_message))}{database.STR_SEPARATOR}{int(bool(self._notify_replace))}{database.STR_SEPARATOR}{int(bool(self._newsletter))}{database.STR_SEPARATOR}{self._family_name}{database.STR_SEPARATOR}{self._first_name}{database.STR_SEPARATOR}{self._residence}{database.STR_SEPARATOR}{self._nationality}{database.STR_SEPARATOR}{self._time_zone}").encode('ascii')


def convert_player(buffer: bytes) -> Player:
    """ To extract an object from database """

    tab = buffer.split(database.BYTES_SEPARATOR)
    identifier = int(tab[0].decode())
    pseudo = tab[1].decode()
    email = tab[2].decode()
    email_confirmed = bool(int(tab[3].decode()))
    notify_deadline = bool(int(tab[4].decode()))
    notify_adjudication = bool(int(tab[5].decode()))
    notify_message = bool(int(tab[6].decode()))
    notify_replace = bool(int(tab[7].decode()))
    newsletter = bool(int(tab[8].decode()))
    family_name = tab[9].decode()
    first_name = tab[10].decode()
    residence = tab[11].decode()
    nationality = tab[12].decode()
    time_zone = tab[13].decode()

    player = Player(identifier, pseudo, email, email_confirmed, notify_deadline, notify_adjudication, notify_message, notify_replace, newsletter, family_name, first_name, residence, nationality, time_zone)
    return player


# Interfaces between python and database
sqlite3.register_adapter(Player, Player.adapt_player)
sqlite3.register_converter('player', convert_player)


if __name__ == '__main__':
    assert False, "Do not run this script"
