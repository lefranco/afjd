#!/usr/bin/env python3


"""
File : populate.py

Data : populate database
"""

import mylogger
import actives
import submissions
import orders
import ownerships
import units
import forbiddens
import reports
import transitions
import games
import messages
import declarations
import allocations
import visits


def populate_transitions() -> None:
    """ inserts these items in database """
    transitions.Transition.create_table()


def populate_reports() -> None:
    """ inserts these items in database """
    reports.Report.create_table()


def populate_actives() -> None:
    """ inserts these items in database """
    actives.Active.create_table()


def populate_submissions() -> None:
    """ inserts these items in database """
    submissions.Submission.create_table()


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


def populate_declarations() -> None:
    """ inserts these items in database """
    declarations.Declaration.create_table()


def populate_messages() -> None:
    """ inserts these items in database """
    messages.Message.create_table()


def populate_allocations() -> None:
    """ inserts these items in database """
    allocations.Allocation.create_table()


def populate_visits() -> None:
    """ inserts these items in database """
    visits.Visit.create_table()


def populate() -> None:
    """ inserts all items in database """

    mylogger.LOGGER.warning("Populating...")

    populate_transitions()
    populate_reports()
    populate_actives()
    populate_submissions()
    populate_orders()
    populate_ownerships()
    populate_units()
    populate_forbiddens()
    populate_games()
    populate_messages()
    populate_declarations()
    populate_allocations()
    populate_visits()


if __name__ == '__main__':
    assert False, "Do not run this script"
