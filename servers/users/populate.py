#!/usr/bin/env python3


"""
File : populate.py

Data : populate database
"""

import mylogger
import users
import logins
import failures
import rescues
import database


def populate_users(sql_executor: database.SqlExecutor) -> None:
    """ inserts these items in database """

    users.User.create_table(sql_executor)


def populate_logins(sql_executor: database.SqlExecutor) -> None:
    """ inserts these items in database """

    logins.Login.create_table(sql_executor)


def populate_failures(sql_executor: database.SqlExecutor) -> None:
    """ inserts these items in database """

    failures.Failure.create_table(sql_executor)


def populate_rescues(sql_executor: database.SqlExecutor) -> None:
    """ inserts these items in database """

    rescues.Rescue.create_table(sql_executor)


def populate(sql_executor: database.SqlExecutor) -> None:
    """ inserts all items in database """

    mylogger.LOGGER.warning("Populating...")
    populate_users(sql_executor)
    populate_logins(sql_executor)
    populate_failures(sql_executor)
    populate_rescues(sql_executor)


if __name__ == '__main__':
    assert False, "Do not run this script"
