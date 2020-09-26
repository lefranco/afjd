#!/usr/bin/env python3


"""
File : populate.py

Data : populate database
"""

import mylogger
import orders
import ownerships
import units
import forbiddens
import allocations
import reports
import games


def populate_reports() -> None:
    """ inserts these items in database """
    reports.Report.create_table()


def populate_orders() -> None:
    """ inserts these items in database """
    orders.Order.create_table()


def populate_ownerships() -> None:
    """ inserts these items in database """
    ownerships.Ownership.create_table()


def populate_units() -> None:
    """ inserts these items in database """
    units.Unit.create_table()


def populate_forbiddens() -> None:
    """ inserts these items in database """
    forbiddens.Forbidden.create_table()


def populate_games() -> None:
    """ inserts these items in database """
    games.Game.create_table()


def populate_allocations() -> None:
    """ inserts these items in database """
    allocations.Allocation.create_table()


def populate() -> None:
    """ inserts all items in database """

    mylogger.LOGGER.warning("Populating...")

    populate_reports()

    populate_orders()

    populate_ownerships()
    populate_units()
    populate_forbiddens()
    populate_games()
    populate_allocations()


if __name__ == '__main__':
    assert False, "Do not run this script"
