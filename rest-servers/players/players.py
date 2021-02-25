#!/usr/bin/env python3


"""
File : players.py

Handles the players
"""
import typing
import sqlite3

import database

# need to have a limit in sizes of fields
LEN_PSEUDO_MAX = 12
LEN_EMAIL_MAX = 30
LEN_EMAIL_CONFIRMED_MAX = 5
LEN_TELEPHONE_MAX = 15
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
    with open(full_name_file, 'r') as file_ptr:
        json_data = json.load(file_ptr)
    assert isinstance(json_data, dict), "File to check countries is not a dict"
    print(f"{json_data=}")
    return country in json_data.values()


class Player:
    """ Class for handling a player """

    @staticmethod
    def free_identifier() -> int:
        """ class free identifier : finds an new identifier from database to use for this object """
        highest_identifier_found = database.sql_execute("SELECT MAX(identifier) AS max_identifier FROM players", None, need_result=True)
        highest_identifier = highest_identifier_found[0][0]  # type: ignore
        if highest_identifier is None:
            return 1
        return highest_identifier + 1  # type: ignore

    @staticmethod
    def find_by_identifier(identifier: int) -> typing.Optional['Player']:
        """ class lookup : finds the object in database from identifier """
        players_found = database.sql_execute("SELECT player_data FROM players where identifier = ?", (identifier,), need_result=True)
        if not players_found:
            return None
        return players_found[0][0]  # type: ignore

    @staticmethod
    def find_by_pseudo(pseudo: str) -> typing.Optional['Player']:
        """ class lookup : finds the object in database from pseudo """
        players_found = database.sql_execute("SELECT player_data FROM players where pseudo = ?", (pseudo,), need_result=True)
        if not players_found:
            return None
        return players_found[0][0]  # type: ignore

    @staticmethod
    def inventory() -> typing.List['Player']:
        """ class inventory : gives a list of all objects in database """
        players_found = database.sql_execute("SELECT player_data FROM players", need_result=True)
        if not players_found:
            return []
        players_list = [p[0] for p in players_found]
        return players_list

    @staticmethod
    def create_table() -> None:
        """ creation of table from scratch """

        database.sql_execute("DROP TABLE IF EXISTS players")
        database.sql_execute("CREATE TABLE players (identifier INT UNIQUE PRIMARY KEY, pseudo STR, player_data player)")
        database.sql_execute("CREATE UNIQUE INDEX pseudo_player ON  players (pseudo)")

    def __init__(self, identifier: int, pseudo: str, email: str, email_confirmed: bool, telephone: str, replace: bool, family_name: str, first_name: str, country: str, time_zone: str) -> None:

        assert isinstance(identifier, int), "identifier must be an int"
        self._identifier = identifier

        assert isinstance(pseudo, str), "pseudo must be a str"
        self._pseudo = pseudo

        self._email = email
        self._email_confirmed = email_confirmed
        self._telephone = telephone
        self._replace = replace
        self._first_name = first_name
        self._family_name = family_name
        self._country = country
        self._time_zone = time_zone

    def update_database(self) -> None:
        """ Pushes changes from object to database """
        database.sql_execute("INSERT OR REPLACE INTO players (identifier, pseudo, player_data) VALUES (?, ?, ?)", (self._identifier, self._pseudo, self))

    def delete_database(self) -> None:
        """ Removes object from database """
        database.sql_execute("DELETE FROM players WHERE identifier = ?", (self._identifier,))

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

        if 'telephone' in json_dict and json_dict['telephone'] is not None and json_dict['telephone'] != self._telephone:
            self._telephone = json_dict['telephone']
            self._telephone = database.sanitize_field(self._telephone)
            self._telephone = self._telephone[:LEN_TELEPHONE_MAX]
            changed = True

        if 'replace' in json_dict and json_dict['replace'] is not None and json_dict['replace'] != self._replace:
            self._replace = json_dict['replace']
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

        if 'country' in json_dict and json_dict['country'] is not None and json_dict['country'] != self._country:
            self._country = json_dict['country']
            self._country = database.sanitize_field(self._country)
            self._country = self._country[:LEN_COUNTRY_MAX]
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
            'telephone': self._telephone,
            'replace': self._replace,
            'family_name': self._family_name,
            'first_name': self._first_name,
            'country': self._country,
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
    def country(self) -> str:
        """ property """
        return self._country

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

    def __str__(self) -> str:
        return f"pseudo={self._pseudo} email={self._email} email_confirmed={self._email_confirmed} telephone={self._telephone} replace={self._replace} family_name={self._family_name} first_name={self._first_name} country={self._country} time_zone={self._time_zone}"

    def adapt_player(self) -> bytes:
        """ To put an object in database """
        return (f"{self._identifier}{database.STR_SEPARATOR}{self._pseudo}{database.STR_SEPARATOR}{self._email}{database.STR_SEPARATOR}{int(bool(self._email_confirmed))}{database.STR_SEPARATOR}{self._telephone}{database.STR_SEPARATOR}{int(bool(self._replace))}{database.STR_SEPARATOR}{self._family_name}{database.STR_SEPARATOR}{self._first_name}{database.STR_SEPARATOR}{self._country}{database.STR_SEPARATOR}{self._time_zone}").encode('ascii')


def convert_player(buffer: bytes) -> Player:
    """ To extract an object from database """

    tab = buffer.split(database.BYTES_SEPARATOR)
    identifier = int(tab[0].decode())
    pseudo = tab[1].decode()
    email = tab[2].decode()
    email_confirmed = bool(int(tab[3].decode()))
    telephone = tab[4].decode()
    replace = bool(int(tab[5].decode()))
    family_name = tab[6].decode()
    first_name = tab[7].decode()
    country = tab[8].decode()
    time_zone = tab[9].decode()
    player = Player(identifier, pseudo, email, email_confirmed, telephone, replace, family_name, first_name, country, time_zone)
    return player


# Interfaces between python and database
sqlite3.register_adapter(Player, Player.adapt_player)
sqlite3.register_converter('player', convert_player)


if __name__ == '__main__':
    assert False, "Do not run this script"
