#!/usr/bin/env python3


"""
File : users.py

Handles the users (the passwords)
"""
import typing
import sqlite3

import database

# need to have a limit in sizes of fields
LEN_USER_NAME_MAX = 12
LEN_PASSWORD_MAX = 20


class User:
    """ Class for handling a User (password) """

    @staticmethod
    def find_by_name(user_name: str) -> typing.Optional['User']:
        """ class lookup : finds the object in database from user_name """
        users_found = database.sql_execute("SELECT user_data FROM users where user_name = ?", (user_name,), need_result=True)
        if not users_found:
            return None
        return users_found[0][0]  # type: ignore

    @staticmethod
    def create_table() -> None:
        """ creation of table from scratch """

        database.sql_execute("DROP TABLE IF EXISTS users")
        database.sql_execute("CREATE TABLE users (user_name STR UNIQUE PRIMARY KEY, user_data user)")

    def __init__(self, user_name: str, pwd_hash: str) -> None:

        assert isinstance(user_name, str), "identifier must be an str"
        self._user_name = user_name

        assert isinstance(pwd_hash, str), "pwd_hash must be a str"
        self._pwd_hash = pwd_hash

    def update_database(self) -> None:
        """ Pushes changes from object to database """
        database.sql_execute("INSERT OR REPLACE INTO users (user_name, user_data) VALUES (?, ?)", (self._user_name, self))

    def delete_database(self) -> None:
        """ Removes object from database """
        database.sql_execute("DELETE FROM users WHERE user_name = ?", (self._user_name,))

    @property
    def user_name(self) -> str:
        """ property """
        return self._user_name

    @property
    def pwd_hash(self) -> str:
        """ property """
        return self._pwd_hash

    @pwd_hash.setter
    def pwd_hash(self, pwd_hash: str) -> None:
        """ setter """
        self._pwd_hash = pwd_hash

    def __str__(self) -> str:
        return f"user_name={self._user_name} pwd_hash={self._pwd_hash}"

    def adapt_user(self) -> bytes:
        """ To put an object in database """
        return (f"{self._user_name}{database.STR_SEPARATOR}{self._pwd_hash}").encode('ascii')


def convert_user(buffer: bytes) -> User:
    """ To extract an object from database """

    tab = buffer.split(database.BYTES_SEPARATOR)
    user_name = tab[0].decode()
    pwd_hash = tab[1].decode()
    user = User(user_name, pwd_hash)
    return user


# Interfaces between python and database
sqlite3.register_adapter(User, User.adapt_user)
sqlite3.register_converter('user', convert_user)


if __name__ == '__main__':
    assert False, "Do not run this script"
