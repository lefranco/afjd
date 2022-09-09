#!/usr/bin/env python3


"""
File : populate.py

Data : populate database
"""

import mylogger
import newss
import news2s
import moderators
import players
import ratings
import database


def populate_newss(sql_executor: database.SqlExecutor) -> None:
    """ inserts these items in database """

    newss.News.create_table(sql_executor)


def populate_news2s(sql_executor: database.SqlExecutor) -> None:
    """ inserts these items in database """

    news2s.News.create_table(sql_executor)


def populate_players(sql_executor: database.SqlExecutor) -> None:
    """ inserts these items in database """

    players.Player.create_table(sql_executor)


def populate_moderators(sql_executor: database.SqlExecutor) -> None:
    """ inserts these items in database """

    moderators.Moderator.create_table(sql_executor)


def populate_ratings(sql_executor: database.SqlExecutor) -> None:
    """ inserts these items in database """

    ratings.Rating.create_table(sql_executor)


def populate(sql_executor: database.SqlExecutor) -> None:
    """ inserts all items in database """

    mylogger.LOGGER.warning("Populating...")

    populate_newss(sql_executor)
    populate_news2s(sql_executor)
    populate_players(sql_executor)
    populate_moderators(sql_executor)
    populate_ratings(sql_executor)


if __name__ == '__main__':
    assert False, "Do not run this script"
