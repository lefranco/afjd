#!/usr/bin/env python3


"""
File : populate.py

Data : populate database
"""

import mylogger
import users
import database


def populate_users(sql_executor: database.SqlExecutor) -> None:
    """ inserts these items in database """

    users.User.create_table(sql_executor)


def populate(sql_executor: database.SqlExecutor) -> None:
    """ inserts all items in database """

    mylogger.LOGGER.warning("Populating...")
    populate_users(sql_executor)


if __name__ == '__main__':
    assert False, "Do not run this script"
