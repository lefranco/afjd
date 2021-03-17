#!/usr/bin/env python3


"""
File : populate.py

Data : populate database
"""

import mylogger
import newss
import players


def populate_newss() -> None:
    """ inserts these items in database """

    newss.News.create_table()


def populate_players() -> None:
    """ inserts these items in database """

    players.Player.create_table()


def populate() -> None:
    """ inserts all items in database """

    mylogger.LOGGER.warning("Populating...")

    populate_newss()
    populate_players()


if __name__ == '__main__':
    assert False, "Do not run this script"
