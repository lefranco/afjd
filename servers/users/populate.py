#!/usr/bin/env python3


"""
File : populate.py

Data : populate database
"""

import mylogger
import users


def populate_users() -> None:
    """ inserts these items in database """

    users.User.create_table()


def populate() -> None:
    """ inserts all items in database """

    mylogger.LOGGER.warning("Populating...")

    populate_users()


if __name__ == '__main__':
    assert False, "Do not run this script"
