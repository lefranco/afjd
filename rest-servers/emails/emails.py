#!/usr/bin/env python3


"""
File : emails.py

Handles the emails
"""
import typing
import sqlite3

import database

# need to have a limit in sizes of fields
LEN_EMAIL_VALUE_MAX = 30
LEN_CODE_MAX = 4


class Email:
    """ Class for handling a Email (code) """

    @staticmethod
    def find_by_value(sql_executor: database.SqlExecutor, email_value: str) -> typing.Optional['Email']:
        """ class lookup : finds the object in database from email_value """
        emails_found = sql_executor.execute("SELECT email_data FROM emails where email_value = ?", (email_value,), need_result=True)
        if not emails_found:
            return None
        return emails_found[0][0]  # type: ignore

    @staticmethod
    def create_table(sql_executor: database.SqlExecutor) -> None:
        """ creation of table from scratch """

        sql_executor.execute("DROP TABLE IF EXISTS emails")
        sql_executor.execute("CREATE TABLE emails (email_value STR UNIQUE PRIMARY KEY, email_data email)")

    def __init__(self, email_value: str, code: int) -> None:

        assert isinstance(email_value, str), "email must be an str"
        self._email_value = email_value

        assert isinstance(code, int), "code must be a int"
        self._code = code

    def update_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Pushes changes from object to database """
        sql_executor.execute("INSERT OR REPLACE INTO emails (email_value, email_data) VALUES (?, ?)", (self._email_value, self))

    def delete_database(self, sql_executor: database.SqlExecutor) -> None:
        """ Removes object from database """
        sql_executor.execute("DELETE FROM emails WHERE email_value = ?", (self._email_value,))

    @property
    def email_value(self) -> str:
        """ property """
        return self._email_value

    @property
    def code(self) -> int:
        """ property """
        return self._code

    def __str__(self) -> str:
        return f"email_value={self._email_value} code={self._code}"

    def adapt_email(self) -> bytes:
        """ To put an object in database """
        return (f"{self._email_value}{database.STR_SEPARATOR}{self._code}").encode('ascii')


def convert_email(buffer: bytes) -> Email:
    """ To extract an object from database """

    tab = buffer.split(database.BYTES_SEPARATOR)
    email_value = tab[0].decode()
    code = int(tab[1].decode())
    email = Email(email_value, code)
    return email


# Interfaces between python and database
sqlite3.register_adapter(Email, Email.adapt_email)
sqlite3.register_converter('email', convert_email)

if __name__ == '__main__':
    assert False, "Do not run this script"
